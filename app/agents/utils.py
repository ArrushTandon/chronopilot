import time
from google import genai
from app.config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_with_retry(contents: str, retries: int = 5, delay: int = 15) -> str:
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI ERROR] {error_str}")

            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < retries - 1:
                    print(f"[RETRY {attempt+1}/{retries}] Model busy, waiting {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    raise Exception("Model unavailable after all retries. Try again in a few minutes.")

            elif "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                raise Exception("API quota exhausted. Resets in ~1 hour. Your code is working correctly.")

            else:
                raise Exception(f"Model error: {error_str}")