# src/pt3/gemini_llm.py
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai.types import Part, UserContent, ModelContent, HttpOptions, GenerateContentConfig
load_dotenv()

# Initialize Client
# Ensure GEMINI_API_KEY
client = genai.Client(
    http_options=HttpOptions(api_version="v1beta"),
)

# --- Path Handling ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SYSTEM_PROMPT_PATH = os.path.join(PROJECT_ROOT, "unified_system_prompt.txt")

try:
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print(f"Warning: Could not find system prompt at {SYSTEM_PROMPT_PATH}")
    SYSTEM_PROMPT = "You are a helpful cooking assistant."


def ask_gemini(
    user_query: str,
    recipe_data: dict,
    curr_idx: int,
    extra_file_uris: list[str] | None = None,
) -> str:
    """
    Send a cooking question to Gemini with context injection.
    """
    extra_file_uris = extra_file_uris or []

    # 1. extract specific text for the current step to help Gemini focus
    steps = recipe_data.get("steps", [])
    current_step_text = "Unknown step"
    
    # Logic to match your step_manager structure
    for st in steps:
        if st.get("step_number") == curr_idx:
            current_step_text = st.get("text") 
            break

    step_context_str = f"User is currently on Step {curr_idx}: {current_step_text}"

    # 2. Serialize recipe to JSON string for the model
    recipe_json_snippet = json.dumps(recipe_data, ensure_ascii=False, indent=2)

    # 3. API Call
    # We use the 'config' parameter to set the system prompt properly
    chat = client.chats.create(
        model="gemini-2.0-flash", 
        config=GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7, # helps keep instructions strict
        ),
        history=[
            UserContent(parts=[Part(text=f"Here is the recipe data I am cooking with:\n{recipe_json_snippet}")]),
            ModelContent(parts=[Part(text="Understood. I have the recipe data and am ready to help.")])
        ],
    )

    try:
        # --- THE FIX IS HERE ---
        # Do not wrap this in UserContent(). Pass the list of texts/parts directly.
        response = chat.send_message(
            message=[
                f"CURRENT STATUS: {step_context_str}", 
                f"USER QUESTION: {user_query}"
            ]
        )
        return response.text or "I'm having trouble thinking right now."
    except Exception as e:
        return f"Gemini API Error: {e}"