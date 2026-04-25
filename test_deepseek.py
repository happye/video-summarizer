import requests
from config import DEEPSEEK_API_KEY

def test_deepseek_connectivity():
    """Test DeepSeek API connectivity and model availability"""
    print("=" * 50)
    print("DeepSeek API Connectivity Test")
    print("=" * 50)

    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY is not set in config.py")
        return False

    print(f"API Key: {DEEPSEEK_API_KEY[:10]}...{DEEPSEEK_API_KEY[-4:]}")
    print()

    # Test 1: Basic connectivity with deepseek-v4-pro
    print("Test 1: Testing deepseek-v4-pro model...")
    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        data = {
            "model": "deepseek-v4-pro",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, please respond with 'DeepSeek API is working!' and nothing else."}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"  Response: {content.strip()}")
        print(f"  Model: {result.get('model', 'unknown')}")
        print(f"  Usage: {result.get('usage', {})}")
        print("  Status: SUCCESS")
        print()
        test1_pass = True
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        print("  Status: FAILED")
        print()
        test1_pass = False

    # Test 2: Test deepseek-v4-flash model
    print("Test 2: Testing deepseek-v4-flash model...")
    try:
        data_flash = {
            "model": "deepseek-v4-flash",
            "messages": [
                {"role": "user", "content": "Say 'Flash model works!'"}
            ],
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False
        }

        response = requests.post(url, headers=headers, json=data_flash, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"  Response: {content.strip()}")
        print(f"  Model: {result.get('model', 'unknown')}")
        print("  Status: SUCCESS")
        print()
        test2_pass = True
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        print("  Status: FAILED (this is OK if you only use pro)")
        print()
        test2_pass = False

    # Test 3: Test long context capability (simulate with a larger prompt)
    print("Test 3: Testing context handling...")
    try:
        from llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient()

        # Check default settings
        print(f"  Model: {client.model}")
        print(f"  Max context messages: {client.max_context_messages}")
        print(f"  Max tokens per request: {client.max_tokens_per_request}")
        print(f"  Timeout: {client.timeout}s")

        # Generate a test response
        response = client.generate("What is your model name and context window size? Answer briefly.", reset_context=True)
        print(f"  Response: {response.strip()}")
        print("  Status: SUCCESS")
        print()
        test3_pass = True
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        print("  Status: FAILED")
        print()
        test3_pass = False

    # Summary
    print("=" * 50)
    print("Test Summary:")
    print(f"  deepseek-v4-pro:   {'PASS' if test1_pass else 'FAIL'}")
    print(f"  deepseek-v4-flash: {'PASS' if test2_pass else 'FAIL'}")
    print(f"  Client integration: {'PASS' if test3_pass else 'FAIL'}")
    print("=" * 50)

    return test1_pass and test3_pass

if __name__ == "__main__":
    success = test_deepseek_connectivity()
    exit(0 if success else 1)
