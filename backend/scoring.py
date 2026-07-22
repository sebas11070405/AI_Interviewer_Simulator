from urllib import response

from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=3,
    timeout=30.0
)
def evaluate_answer(question: str, answer: str, topic: str = "software engineering"):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": f"""
                You are an interviewer for the topic: {topic}.
                Evaluate the following answer.
                Return ONLY JSON:
                {{
                    "score": 0,
                    "explanation": ""
                }}
                """
            },
            {
                "role": "user",
                "content": f"Question: {question}\nAnswer: {answer}"
            }
        ]
    )

    content = response.choices[0].message.content.strip()
    
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    return json.loads(content)