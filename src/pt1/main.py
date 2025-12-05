# src/pt1/main.py
import os
import sys
import time
import json
import re
from typing import Tuple

# -----------------------------------------------------------------------------
# 1. PATH SETUP
# Ensures we can import modules from parent directories and sibling src/ folders
# -----------------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# -----------------------------------------------------------------------------
# 2. IMPORTS
# -----------------------------------------------------------------------------
try:
    import recipe_scraper
    import recipe_parser
    import step_manager
    from pt3.gemini_llm import ask_gemini
except ImportError as e:
    print(f"CRITICAL ERROR: Could not import necessary modules. {e}")
    print(f"Debug Paths: ROOT={PROJECT_ROOT}, SRC={SRC_DIR}")
    sys.exit(1)


# -----------------------------------------------------------------------------
# 3. GLOBAL CONFIG & HELPERS
# -----------------------------------------------------------------------------
_DELAY_MULTIPLIER = 1.0  # Set to 0.0 to skip delays during testing

def slow_print(*args, delay=0.02):
    """Prints text character-by-character for a 'typing' effect."""
    text = ''.join(str(arg) for arg in args)
    for char in text:
        print(char, end='', flush=True)
        time.sleep(_DELAY_MULTIPLIER * delay)
    print()

def word_print(*args, delay=0.15):
    """Prints word-by-word."""
    text = ' '.join(str(arg) for arg in args)
    words = text.split()
    for word in words:
        print(word, end=' ', flush=True)
        time.sleep(_DELAY_MULTIPLIER * delay)
    print() 

def tactical_pause(seconds=0.35):
    time.sleep(_DELAY_MULTIPLIER * seconds)

# -----------------------------------------------------------------------------
# 4. CORE LOGIC
# -----------------------------------------------------------------------------

def load_recipe_data():
    """Safely loads recipe.json"""
    path = os.path.join(PROJECT_ROOT, "recipe.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def scrape_and_parse(url: str):
    recipe_scraper.main(url)
    recipe_parser.main()
    step_manager.main()
    slow_print("Scraping and parsing complete!")

def handle_step_query(query: str, recipe_data: dict, curr_idx: int) -> Tuple[bool, int, str]:
    """
    LAYER 1: LOCAL NAVIGATION
    Strictly handles moving between steps so the user doesn't get lost.
    Returns: (handled: bool, new_index: int, output_text: str)
    """
    steps = recipe_data.get("steps", [])
    total_steps = len(steps)
    
    q = query.lower().strip()
    
    # Navigation Keywords
    next_kw = ["next", "forward", "advance", "go on", "after that"]
    prev_kw = ["previous", "prev", "back", "last step", "go back", "before that"]
    start_kw = ["start", "begin", "first step"]
    repeat_kw = ["repeat", "say that again", "what was that"]

    output = ""
    new_idx = curr_idx
    handled = False

    # 1. Handle NEXT
    if any(k in q for k in next_kw):
        if curr_idx < total_steps:
            new_idx += 1
            handled = True
        else:
            output = "You are already at the last step!"
            handled = True
            
    # 2. Handle PREVIOUS
    elif any(k in q for k in prev_kw):
        if curr_idx > 1:
            new_idx -= 1
            handled = True
        else:
            output = "You are currently at the first step."
            handled = True

    # 3. Handle START
    elif any(k in q for k in start_kw):
        new_idx = 1
        handled = True

    # 4. Handle REPEAT (Stay on current step, but trigger print)
    elif any(k in q for k in repeat_kw):
        handled = True
        # new_idx remains same

    # Retrieve Text for the (potentially new) step
    if handled:
        # Step numbers usually 1-based. List index is 0-based.
        # We search for the dict with "step_number" == new_idx
        step_obj = next((s for s in steps if s["step_number"] == new_idx), None)
        
        if step_obj:
            # Prefer 'text', fallback to 'description'
            desc = step_obj.get("text") or step_obj.get("description")
            output = f"\n[Step {new_idx}/{total_steps}]: {desc}"
        else:
            output = "Error: Step not found."

    return handled, new_idx, output

def query_handler(recipe_data):
    """
    The Main Interaction Loop.
    1. Check for Exit.
    2. Check for Navigation (Local).
    3. Delegate to Gemini (AI).
    """
    
    slow_print("\n----------------------------------------------------")
    slow_print(" RECIPE ASSISTANT INITIALIZED")
    slow_print("----------------------------------------------------")
    slow_print(" Commands: 'next', 'back', 'repeat', 'exit'")
    
    idx = 1
    
    # Print the first step automatically to start
    _, _, initial_text = handle_step_query("start", recipe_data, 1)
    word_print(initial_text)

    while True:
        query = input("\nYou: ").strip()
        
        if query.lower() in ['exit', 'quit']:
            slow_print("Goodbye! Happy cooking!")
            break
        
        if not query:
            continue

        # --- LAYER 1: LOCAL NAVIGATION ---
        handled, idx, output = handle_step_query(query, recipe_data, idx)
        
        if handled:
            word_print(output)
            continue # Loop back, don't ask Gemini

        # --- LAYER 2: GEMINI AI ---
        slow_print("...", delay=0.1) # Thinking indicator
        
        try:
            # We pass the full recipe + current index to the AI
            answer = ask_gemini(
                user_query=query, 
                recipe_data=recipe_data, 
                curr_idx=idx
            )
            print()
            word_print("Assistant:", answer)
            
        except Exception as e:
            print(f"\n[System Error]: {e}")
            slow_print("I'm having trouble connecting to the AI brain.")

def startup_base():
    """Initial setup: URL input, Scraping, Parsing, Display Summary"""
    slow_print("What recipe would you like to cook today?")
    url = input("\nEnter recipe url (or press Enter to use existing recipe.json): ").strip()
    
    if url:
        slow_print("\nGreat! Let's scrape and parse this delicious recipe!")
        tactical_pause()
        scrape_and_parse(url)
        tactical_pause(3)
    
    # Reload data here to ensure we have the fresh scrape results
    recipe_data = load_recipe_data()
    
    if not recipe_data:
        slow_print("Error: No recipe.json found. Please provide a URL first.")
        return None

    slow_print("Let's see what we have!")
    word_print("\nRecipe Details:\n", delay=0.3)
    word_print("Title:", recipe_data.get("title", "Unknown"))
    word_print("Total time:", recipe_data.get("total_time", "Unknown"))
    word_print("Yield:", recipe_data.get("yield", "Unknown"))
    
    word_print("\nIngredients List:")
    for ingredient in recipe_data.get("ingredients", []):
        # Handle cases where ingredient might be a string or a dict
        if isinstance(ingredient, dict):
            # Combine qty, unit, name
            line = f"- {ingredient.get('qty', '')} {ingredient.get('unit', '')} {ingredient.get('name', '')}"
            print(line)
        else:
            print(f"- {ingredient}")
        time.sleep(0.05)
        
    print("\n")
    return recipe_data

def main():
    recipe_data = startup_base()
    
    if not recipe_data:
        return

    slow_print("\nWould you like to start cooking?")
    yes_or_no = input(" y/n : ").strip()
    
    if yes_or_no.lower() in ['y', 'yes', 'sure', 'yeah']:
        query_handler(recipe_data)
    elif yes_or_no.lower() in ['n', 'no', 'nah', 'nope']:
        slow_print("Alright! Enjoy your cooking!")
    else:
        print("Invalid input. Please enter 'y' or 'n'.")

if __name__ == "__main__":
    main()