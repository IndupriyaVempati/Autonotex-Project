import os
from dotenv import load_dotenv
from groq import Groq

# Force reload of .env
load_dotenv(override=True)

key = os.getenv("GROQ_API_KEY")

print("\n" + "="*50)
print(f"Testing API Key from environment...")
if not key:
    print("ERROR: No GROQ_API_KEY found in environment variables.")
    print("Make sure you have a .env file in this folder with:")
    print("GROQ_API_KEY=gsk_...")
else:
    print(f"Key found: {key[:4]}...{key[-4:]}")
    
    try:
        client = Groq(api_key=key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama-3.3-70b-versatile",
        )
        print("SUCCESS! API Key is working.")
        print(f"Response: {chat_completion.choices[0].message.content}")
    except Exception as e:
        print(f"FAILURE: API Key rejected by Groq.")
        print(f"Error details: {e}")

print("="*50 + "\n")
