import requests

# 直接使用API密钥进行测试
api_key = "sk-vOKi7fmVbQEZHg4LWpa7bCpHXbh42X7aYWUsHEQ3sB28xLGK"

def test_kimi_api_simple():
    """Test Kimi API connection with minimal parameters"""
    if not api_key:
        print("Error: API key is not set")
        return
    
    try:
        url = "https://api.moonshot.cn/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "moonshot-v1-8k",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello"
                }
            ]
        }
        
        print("Testing Kimi API connection with minimal parameters...")
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
    test_kimi_api_simple()