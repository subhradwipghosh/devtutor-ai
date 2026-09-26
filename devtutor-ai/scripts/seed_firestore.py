# Copyright 2026 Google LLC
# Seed Firestore collection with educational coding topics.

from google.cloud import firestore

# IMPORTANT: Project ID MUST be hardcoded as a string (project ID, NOT project number)
FIRESTORE_PROJECT = "qwiklabs-gcp-02-9bbf923d4897"

def seed_topics():
    db = firestore.Client(project=FIRESTORE_PROJECT, database="(default)")
    topics_ref = db.collection("topics")

    sample_topics = [
        {
            "id": "python_asyncio",
            "title": "Python Asyncio & Event Loops",
            "category": "Python",
            "difficulty": "Intermediate",
            "summary": "Asynchronous I/O, coroutines, and event loops in Python using async/await syntax.",
            "key_concepts": ["coroutines", "async/await", "EventLoop", "Task", "Future"],
            "code_example": "import asyncio\nasync def main():\n    print('Hello')\n    await asyncio.sleep(1)\n    print('World')\nasyncio.run(main())"
        },
        {
            "id": "fastapi_fundamentals",
            "title": "FastAPI Building Blocks",
            "category": "Python Frameworks",
            "difficulty": "Beginner",
            "summary": "Modern, fast web framework for building APIs with Python 3.8+ based on standard Pydantic models & OpenAPI.",
            "key_concepts": ["Path Parameters", "Pydantic Models", "Dependency Injection", "OpenAPI"],
            "code_example": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}"
        },
        {
            "id": "react_hooks",
            "title": "React Hooks Essentials",
            "category": "Frontend",
            "difficulty": "Beginner",
            "summary": "State and lifecycle features in React functional components using useState, useEffect, and custom hooks.",
            "key_concepts": ["useState", "useEffect", "useContext", "Custom Hooks"],
            "code_example": "import React, { useState } from 'react';\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return <button onClick={() => setCount(count + 1)}>Count: {count}</button>;\n}"
        },
        {
            "id": "docker_basics",
            "title": "Docker & Containerization",
            "category": "DevOps",
            "difficulty": "Beginner",
            "summary": "Containerizing applications using Dockerfiles, images, and containers for consistent execution environments.",
            "key_concepts": ["Dockerfile", "Image", "Container", "Port Mapping", "Volume"],
            "code_example": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"main.py\"]"
        },
        {
            "id": "c_programming_basics",
            "title": "C Language Foundations & Pointers",
            "category": "C / Systems",
            "difficulty": "Beginner",
            "summary": "System-level programming in C including memory management, pointers, structs, and header files.",
            "key_concepts": ["Pointers", "Memory Allocation", "Structs", "Headers", "GCC"],
            "code_example": "#include <stdio.stdio.h>\nint main() {\n    printf(\"Hello, C World!\\n\");\n    return 0;\n}"
        },
        {
            "id": "csharp_dotnet",
            "title": "C# & .NET Core Essentials",
            "category": "C# / .NET",
            "difficulty": "Beginner",
            "summary": "Object-oriented programming in C# with LINQ, properties, async/await, and .NET runtime capabilities.",
            "key_concepts": ["Classes & Interfaces", "LINQ Queries", "Properties", "Async/Await", "NuGet"],
            "code_example": "using System;\nclass Program {\n    static void Main() {\n        Console.WriteLine(\"Hello, .NET!\");\n    }\n}"
        },
        {
            "id": "javascript_modern",
            "title": "Modern JavaScript (ES6+)",
            "category": "JavaScript",
            "difficulty": "Beginner",
            "summary": "Core language features of modern JS including promises, arrow functions, destructuring, and ES modules.",
            "key_concepts": ["Promises & Async/Await", "Arrow Functions", "Destructuring", "Modules", "Closures"],
            "code_example": "const fetchData = async () => {\n  const res = await fetch('https://api.example.com');\n  return res.json();\n};"
        },
        {
            "id": "sql_server_queries",
            "title": "SQL Server T-SQL & Indexing",
            "category": "Databases",
            "difficulty": "Intermediate",
            "summary": "Microsoft SQL Server database management using T-SQL, joins, stored procedures, and index optimization.",
            "key_concepts": ["T-SQL Joins", "Clustered Indexes", "Stored Procedures", "Transactions", "Execution Plans"],
            "code_example": "SELECT p.Name, c.CategoryName\nFROM Products p\nINNER JOIN Categories c ON p.CategoryId = c.CategoryId\nWHERE p.Price > 50;"
        }
    ]

    print(f"Seeding {len(sample_topics)} topics into Firestore project '{FIRESTORE_PROJECT}'...")
    for topic in sample_topics:
        topic_id = topic["id"]
        topics_ref.document(topic_id).set(topic)
        print(f"  ✓ Seeded topic: {topic['title']} ({topic_id})")

    print("Seeding complete! ✅")

if __name__ == "__main__":
    seed_topics()
