"""
Checks that Gemini, Groq, and Qdrant are all reachable using the keys in
.env, before touching the actual pipeline code.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def check_gemini():
    from google import genai

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY missing from .env")
        return False
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(model="gemini-3.6-flash", contents="Say 'ok' and nothing else.")
        print(f"Gemini responded: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"Gemini failed: {e}")
        return False


def check_groq():
    from groq import Groq

    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("GROQ_API_KEY missing from .env")
        return False
    try:
        client = Groq(api_key=key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'ok' and nothing else."}],
        )
        print(f"Groq responded: {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        print(f"Groq failed: {e}")
        return False


def check_qdrant():
    from qdrant_client import QdrantClient

    url, key = os.getenv("QDRANT_URL"), os.getenv("QDRANT_API_KEY")
    if not url or not key:
        print("QDRANT_URL or QDRANT_API_KEY missing from .env")
        return False
    try:
        client = QdrantClient(url=url, api_key=key)
        collections = client.get_collections()
        print(f"Qdrant connected. Existing collections: {collections.collections}")
        return True
    except Exception as e:
        print(f"Qdrant failed: {e}")
        return False


if __name__ == "__main__":
    print("Checking Gemini...")
    gemini_ok = check_gemini()
    print("\nChecking Groq...")
    groq_ok = check_groq()
    print("\nChecking Qdrant...")
    qdrant_ok = check_qdrant()

    print("\n--- Summary ---")
    if gemini_ok and groq_ok and qdrant_ok:
        print("All three services are working.")
    else:
        print("Fix the failures above before continuing.")
