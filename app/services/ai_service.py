import os
import json
from groq import Groq
from app.prompts.main.prompt import get_prompt

client = Groq(api_key=os.getenv("GROQ_API_KEY") or "")


async def classify_message(source: str, message: str) -> dict:
    prompt = get_prompt(source, message)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON. No markdown. No explanation.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise Exception("No response from Groq")

    cleaned = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        raise Exception(f"Invalid JSON from Groq: {cleaned}")