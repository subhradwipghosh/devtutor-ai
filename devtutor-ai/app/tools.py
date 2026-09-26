# Copyright 2026 Google LLC
# Firestore and utility tools for DevTutor AI agent

import json
import os
import urllib.parse
import urllib.request
import uuid

from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types

# HARDCODED constants as required for Agent Platform compatibility
FIRESTORE_PROJECT = "qwiklabs-gcp-02-9bbf923d4897"
GCS_BUCKET_NAME = "devtutor-ai-media-9bbf923d4897"


def get_firestore_client():
    return firestore.Client(project=FIRESTORE_PROJECT, database="(default)")


def get_topic_details(topic_id: str) -> dict:
    """Fetch details for a specific educational topic or learning module from Firestore.

    Args:
        topic_id: The unique identifier of the topic (e.g., 'python_asyncio', 'fastapi_fundamentals', 'react_hooks').

    Returns:
        A dictionary containing the topic details or error message.
    """
    try:
        db = get_firestore_client()
        doc = db.collection("topics").document(topic_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return {"error": f"Topic '{topic_id}' not found."}
    except Exception as e:
        return {"error": f"Failed to retrieve topic: {str(e)}"}


def list_topics(category: str = "") -> list[dict]:
    """List available learning topics from Firestore, optionally filtered by category.

    Args:
        category: Optional category filter (e.g. 'Python', 'Frontend', 'DevOps'). Leave empty to list all.

    Returns:
        A list of topic summary dictionaries.
    """
    try:
        db = get_firestore_client()
        topics_ref = db.collection("topics")
        docs = topics_ref.where("category", "==", category).stream() if category else topics_ref.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results
    except Exception as e:
        return [{"error": f"Failed to list topics: {str(e)}"}]


def add_topic(
    topic_id: str,
    title: str,
    category: str,
    summary: str,
    difficulty: str = "Beginner",
    key_concepts: list[str] = None,
    code_example: str = ""
) -> dict:
    """Add or update an educational topic in the Firestore topics collection.

    Args:
        topic_id: Unique key for topic.
        title: Display title.
        category: Domain/Category.
        summary: Brief explanation.
        difficulty: Difficulty level ('Beginner', 'Intermediate', 'Advanced').
        key_concepts: List of key vocabulary/concepts.
        code_example: Code snippet.

    Returns:
        Confirmation dictionary.
    """
    try:
        db = get_firestore_client()
        doc_data = {
            "id": topic_id,
            "title": title,
            "category": category,
            "summary": summary,
            "difficulty": difficulty,
            "key_concepts": key_concepts or [],
            "code_example": code_example,
        }
        db.collection("topics").document(topic_id).set(doc_data)
        return {"status": "success", "message": f"Saved topic '{title}' ({topic_id})."}
    except Exception as e:
        return {"error": f"Failed to save topic: {str(e)}"}


def record_student_progress(student_id: str, topic_id: str, mastery_score: int, status: str = "completed") -> dict:
    """Record or update a student's learning progress and mastery score in Firestore.

    Args:
        student_id: Unique ID of the student (e.g. 'student_123').
        topic_id: ID of the topic completed or practiced.
        mastery_score: Score from 0 to 100.
        status: Progress status ('in_progress', 'completed', 'needs_review').

    Returns:
        Status result dictionary.
    """
    try:
        db = get_firestore_client()
        doc_id = f"{student_id}_{topic_id}"
        record = {
            "student_id": student_id,
            "topic_id": topic_id,
            "mastery_score": mastery_score,
            "status": status,
        }
        db.collection("user_progress").document(doc_id).set(record)
        return {"status": "success", "message": f"Recorded progress for {student_id} on {topic_id} (score: {mastery_score}%)."}
    except Exception as e:
        return {"error": f"Failed to record progress: {str(e)}"}


def evaluate_quiz_answer(topic_id: str, user_answer: str) -> dict:
    """Evaluate a student's answer against key concepts for a topic in Firestore.

    Args:
        topic_id: Topic ID being tested.
        user_answer: The student's written response or code snippet.

    Returns:
        Evaluation dictionary with topic concepts and feedback recommendation.
    """
    topic = get_topic_details(topic_id)
    if "error" in topic:
        return topic
    
    concepts = topic.get("key_concepts", [])
    matched = [c for c in concepts if c.lower() in user_answer.lower()]
    score = int((len(matched) / max(len(concepts), 1)) * 100)
    
    return {
        "topic_id": topic_id,
        "matched_concepts": matched,
        "missing_concepts": [c for c in concepts if c not in matched],
        "estimated_score": score,
        "feedback": f"Matched {len(matched)} of {len(concepts)} key concepts."
    }


def fetch_code_cheatsheet(topic_id: str) -> dict:
    """Fetch a quick syntax cheat sheet and code example for a topic.

    Args:
        topic_id: Topic ID to look up.

    Returns:
        Cheat sheet dictionary containing title, key concepts, and code example.
    """
    topic = get_topic_details(topic_id)
    if "error" in topic:
        return topic
    
    return {
        "title": topic.get("title"),
        "key_concepts": topic.get("key_concepts", []),
        "code_example": topic.get("code_example", "# No code example available"),
    }


def fetch_official_docs(topic: str, framework_or_language: str = "") -> dict:
    """Fetch official documentation references and resources for a study topic.

    Args:
        topic: Topic or concept name (e.g., 'asyncio', 'useState', 'T-SQL joins').
        framework_or_language: Optional language/framework context (e.g. 'Python', 'React', 'SQL Server').

    Returns:
        Dictionary containing official doc links and reference guidelines.
    """
    query_str = f"{framework_or_language} {topic}".strip()
    
    doc_map = {
        "python": "https://docs.python.org/3/",
        "react": "https://react.dev/reference/react",
        "fastapi": "https://fastapi.tiangolo.com/",
        "docker": "https://docs.docker.com/",
        "c": "https://en.cppreference.com/w/c",
        "c#": "https://learn.microsoft.com/en-us/dotnet/csharp/",
        "javascript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "sql server": "https://learn.microsoft.com/en-us/sql/sql-server/",
    }
    
    lang_key = framework_or_language.lower()
    base_url = doc_map.get(lang_key, f"https://devdocs.io/#q={query_str}")
    
    return {
        "topic": topic,
        "framework_or_language": framework_or_language,
        "search_query": query_str,
        "official_doc_url": base_url,
        "tip": f"Consult official documentation at {base_url} for the latest syntax and API specifications."
    }


def search_github_repositories(query: str, language: str = "") -> list[dict]:
    """Search GitHub for top public open-source repositories and starter templates for a study topic.

    Args:
        query: Search topic or keyword (e.g. 'asyncio examples', 'fastapi starter', 'react hooks tutorial').
        language: Optional programming language filter (e.g. 'python', 'javascript', 'csharp').

    Returns:
        List of repository dictionaries with name, description, star count, and repository URL.
    """
    try:
        q = f"{query} language:{language}".strip() if language else query
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=5"
        
        headers = {"User-Agent": "DevTutor-AI-Agent"}
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            items = data.get("items", [])
            return [
                {
                    "name": item.get("full_name"),
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count"),
                    "url": item.get("html_url"),
                }
                for item in items
            ]
    except Exception as e:
        return [{"error": f"Failed to search GitHub repositories: {str(e)}"}]


async def generate_concept_diagram(prompt: str, tool_context: ToolContext) -> dict:
    """Generate an educational diagram, architecture flowchart, or infographic using gemini-3.1-flash-lite-image in global region.

    Saves the generated image as an artifact for the Playground and uploads it directly to Cloud Storage.

    Args:
        prompt: Description of the educational diagram or technical concept visualization.
        tool_context: ADK ToolContext used to register and save the artifact.

    Returns:
        Dictionary containing the public image URL and metadata.
    """
    try:
        genai_client = genai.Client(vertexai=True, location="global")
        
        enhanced_prompt = f"Educational technical diagram, clean infographic style, software architecture visualization: {prompt}"
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=enhanced_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )
        
        image_part = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_part = part
                break
                
        if not image_part or not image_part.inline_data:
            return {"error": "Failed to generate image from model."}
            
        image_bytes = image_part.inline_data.data
        mime_type = image_part.inline_data.mime_type or "image/jpeg"
        ext = "png" if "png" in mime_type else "jpg"
        
        filename = f"diagram_{uuid.uuid4().hex[:8]}.{ext}"
        
        # (1) Save artifact for Playground
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        
        # (2) Upload directly to Cloud Storage bucket without local file writes
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        
        return {
            "status": "success",
            "filename": filename,
            "public_url": public_url,
            "message": f"Generated educational diagram saved as artifact '{filename}' and published to Cloud Storage.",
        }
    except Exception as e:
        return {"error": f"Failed to generate concept diagram: {str(e)}"}


async def generate_topic_video(prompt: str, tool_context: ToolContext) -> dict:
    """Generate a short video for an educational topic or programming concept using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the generated video as an artifact for the Playground and uploads it directly to Cloud Storage.

    Args:
        prompt: Detailed description or topic name for the educational video animation.
        tool_context: ADK ToolContext used to register and save the video artifact.

    Returns:
        Dictionary containing the public Cloud Storage HTTPS video URL and artifact metadata.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")
        
        enhanced_prompt = f"Educational 3-second animated video tutorial on software development and computer science: {prompt}"
        
        response = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=enhanced_prompt,
            response_format={"type": "video"}
        )
        
        out_video = getattr(response, "output_video", None)
        if not out_video:
            return {"error": "No output_video received from gemini-omni-flash-preview."}
            
        video_bytes = getattr(out_video, "data", None) or getattr(out_video, "video_bytes", None) or getattr(out_video, "bytes", None)
        if not video_bytes:
            return {"error": "Failed to extract video bytes from output_video."}
            
        if isinstance(video_bytes, str):
            import base64
            try:
                video_bytes = base64.b64decode(video_bytes)
            except Exception:
                pass
            
        mime_type = getattr(out_video, "mime_type", None) or "video/mp4"
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        
        # (1) Save video as artifact for Playground
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)
        
        # (2) Upload decoded video bytes directly to Cloud Storage bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)
        
        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        
        return {
            "status": "success",
            "filename": filename,
            "public_url": public_url,
            "message": f"Generated educational video saved as artifact '{filename}' and published to Cloud Storage.",
        }
    except Exception as e:
        return {"error": f"Failed to generate topic video: {str(e)}"}

