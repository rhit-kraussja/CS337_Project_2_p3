from dotenv import load_dotenv
import os
from google import genai

# Load environment variables from the .env file
load_dotenv()

# Retrieve the Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")

# Initialize the Gemini client
client = genai.Client(api_key=api_key)

# Load system prompt
system_prompt = open("unified_system_prompt.txt").read()

# Create an ongoing chat
chat = client.chats.create(
    model="gemini-2.5-flash",
    history=[
        {"role": "model", "parts": [{"text": system_prompt}]}
    ]
)

print("Gemini assistant initialized. Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() in {"exit", "quit"}:
        break

    # Print the model's response text
    response = chat.send_message(user_input)
    print("Assistant: ", response.text)