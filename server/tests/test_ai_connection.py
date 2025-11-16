import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.simple_config import config
from openai import OpenAI

def test_openai_connection():
    """Test OpenAI connection and API key."""
    print("Testing OpenAI connection...")
    print(f"API Key configured: {'Yes' if config.OPENAI_API_KEY else 'No'}")
    print(f"API Key (first 10 chars): {config.OPENAI_API_KEY[:10]}..." if config.OPENAI_API_KEY else "No API key")
    print(f"Model: {config.OPENAI_MODEL}")
    
    if not config.OPENAI_API_KEY:
        print("Error: OpenAI API key is not configured!")
        return False
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Test with a simple request
        print("\nTesting API call...")
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in Hebrew"}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        print("OpenAI connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"Error connecting to OpenAI: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai_connection()