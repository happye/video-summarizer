import ollama
from config import OLLAMA_MODEL

def ollama_generate(prompt):
    """Generate text using Ollama local model"""
    try:
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        return response.get("response", "")
    except Exception as e:
        raise Exception(f"Error generating text with Ollama: {str(e)}")
