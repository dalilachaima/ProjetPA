
from dotenv import load_dotenv 
from google import genai
import os
load_dotenv() 
client = genai.Client() 

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="donne moi une question avec 4 propositions 3 fausses et 1 bonne"
)

print(response.text)