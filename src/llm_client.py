import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def call_llm(prompt: str,
             system_instruction: str = None,
             temperature: float = 0.1) -> str:
    """
    Calls the local Ollama model.
    """

    full_prompt = ""

    if system_instruction:
        full_prompt += system_instruction + "\n\n"

    full_prompt += prompt

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            },
            timeout=120
        )

        response.raise_for_status()

        return response.json()["response"].strip()

    except Exception as e:
        print("Ollama Error:", e)
        return "ERROR"