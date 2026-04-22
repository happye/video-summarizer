import requests
from config import KIMI_API_KEY

def test_kimi_api_bibi():
    """Test Kimi API connection using BibiGPT's configuration"""
    if not KIMI_API_KEY:
        print("Error: Kimi API key is not set in config.py")
        return
    
    try:
        url = "https://api.moonshot.cn/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KIMI_API_KEY}"
        }
        data = {
            "model": "kimi-k2.6",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, Kimi!"
                }
            ]
        }
        
        print("Testing Kimi API connection with BibiGPT's configuration...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return
        
        result = response.json()
        print("API call successful!")
        print(f"Response: {result['choices'][0]['message']['content']}")
        
    except Exception as e:
        print(f"Error testing Kimi API: {str(e)}")

if __name__ == "__main__":
    test_kimi_api_bibi()