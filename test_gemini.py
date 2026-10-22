
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API key not found. Please check the .env file.")
else:
    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
           model="gemini-3.5-flash-lite",
            contents="Reply with: Gemini API is working!"
        )

        print(response.text)

    except Exception as error:
        print("Gemini API test failed.")
        print(error)
