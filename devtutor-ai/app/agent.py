# ruff: noqa
# Copyright 2026 Google LLC
# DevTutor AI Agent Definition

import json
import logging
from pathlib import Path

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_topic,
    evaluate_quiz_answer,
    fetch_code_cheatsheet,
    fetch_official_docs,
    generate_concept_diagram,
    generate_topic_video,
    get_topic_details,
    list_topics,
    record_student_progress,
    search_github_repositories,
)

logger = logging.getLogger(__name__)

# Constants for project and Memory Bank / Agent Engine
PROJECT_ID = "qwiklabs-gcp-02-9bbf923d4897"
LOCATION = "us-east1"
MEMORY_BANK_ID = "4977381386802429952"

# Load Agent Engine resource name from deployment_metadata.json if present
agent_engine_id = None
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
if metadata_file.exists():
    try:
        with open(metadata_file) as f:
            meta = json.load(f)
            agent_engine_id = meta.get("remote_agent_runtime_id")
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_id)

# Memory service configuration for redeploy later
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=MEMORY_BANK_ID,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: Send the turn session to Memory Bank after each turn to extract durable user facts and preferences."""
    try:
        await callback_context.add_session_to_memory()
    except Exception as exc:
        logger.warning("Memory Bank extraction skipped: %s", exc)
    return None


# Build A2UI System Prompt using A2uiSchemaManager version 0.8 & BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are DevTutor AI, an interactive educational tutor designed to help "
        "developers learn programming languages, frameworks, and technical topics. "
        "You remember user preferences, learning goals, and past session details. "
        "You can generate educational diagrams using `generate_concept_diagram` and short "
        "animated explanation videos using `generate_topic_video`. When asked to create a video, "
        "animation, or visual tutorial, always invoke `generate_topic_video`. "
        "Whenever `generate_topic_video` or `generate_concept_diagram` returns a public_url, "
        "ALWAYS include the full public_url in your text response so the user can view/play it. "
        "You can run Python code safely in a sandbox using code blocks (```python ... ```) to test code or verify outputs."
    ),
    workflow_description="Analyze the user request, call function tools if needed, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_topics,
        get_topic_details,
        add_topic,
        record_student_progress,
        evaluate_quiz_answer,
        fetch_code_cheatsheet,
        fetch_official_docs,
        search_github_repositories,
        generate_concept_diagram,
        generate_topic_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
