import requests
from config import DEEPSEEK_API_KEY

def deepseek_generate(prompt):
    """Generate text using DeepSeek API"""
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API key is not set in config.py")
    
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"Error generating text with DeepSeek: {str(e)}")
