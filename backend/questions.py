from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

def get_questions():
    return [
        "Explain normalization.",
        "What is deadlock?",
        "Difference between TCP and UDP?"
    ]

def generate_questions():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        max_retries=3,
        timeout=30.0
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
                You are a software engineering interviewer.

                Generate exactly 5 technical interview questions.

                Rules:
                - Return ONLY the questions.
                - One question per line.
                - No numbering.
                - No explanations.
                - No expected answers.
                - No markdown.
                """
            }
        ]
    )

    return response.choices[0].message.content.split("\n")