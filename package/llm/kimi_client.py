import requests
from config import KIMI_API_KEY
import time

class KimiClient:
    def __init__(self):
        self.messages = []
        self.max_retries = 3
        self.timeout = 120
        self.retry_delay = 5
    
    def generate(self, prompt, reset_context=False):
        """Generate text using Kimi API with context management"""
        if not KIMI_API_KEY:
            raise ValueError("Kimi API key is not set in config.py")
        
        if reset_context:
            self.messages = []
        
        # Add user message to context
        self.messages.append({
            "role": "user",
            "content": prompt
        })
        
        for attempt in range(self.max_retries):
            try:
                url = "https://api.moonshot.cn/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {KIMI_API_KEY}"
                }
                data = {
                    "model": "kimi-k2.6",
                    "messages": self.messages,
                    "timeout": self.timeout
                }
                
                print(f"Attempt {attempt + 1}/{self.max_retries}: Sending request to Kimi API...")
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
                
                if response.status_code != 200:
                    print(f"Kimi API Error: {response.status_code} - {response.text}")
                response.raise_for_status()
                
                result = response.json()
                assistant_message = result["choices"][0]["message"]
                
                # Add assistant response to context
                self.messages.append(assistant_message)
                
                return assistant_message["content"]
            except requests.exceptions.Timeout as e:
                print(f"Timeout error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # 指数退避
                else:
                    raise Exception(f"Error generating text with Kimi after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Error generating text with Kimi: {str(e)}")

def kimi_generate(prompt):
    """Backward compatibility function"""
    client = KimiClient()
    return client.generate(prompt, reset_context=True)
