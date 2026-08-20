import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")


def generate_llm_response(prompt):
    if not LLM_PROVIDER:
        raise ValueError(
            "LLM_PROVIDER is not configured."
        )

    if not LLM_API_KEY:
        raise ValueError(
            "LLM_API_KEY is not configured."
        )

    if not LLM_MODEL:
        raise ValueError(
            "LLM_MODEL is not configured."
        )

    if LLM_PROVIDER == "groq":
        client = Groq(
            api_key=LLM_API_KEY
        )

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content

    raise ValueError(
        f"Unsupported LLM provider: {LLM_PROVIDER}"
    )