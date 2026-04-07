from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    base_url=settings.lmstudio_base_url,
    api_key=settings.lmstudio_api_key
)

def small_language_connection():
    response = client.chat.completions.create(
        model=settings.lmstudio_model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for testing the connection to the small language model."},
            {"role": "user", "content": "Please respond with a simple message to confirm the connection."}
        ],
        temperature=0.2 # Lower temperature for more deterministic responses        
    )
    return response.choices[0].message.content.strip()