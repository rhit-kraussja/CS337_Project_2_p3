Project: Recipe Assistant — CS337_Project_2_p3
GitHub: https://github.com/rhit-kraussja/CS337_Project_2_p3

Setup
- 3.11 recommended
- Create venv and install requirements:
  python -m venv .venv && source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
- (Optional) GenAI for Gemini: python -m pip install --upgrade google-genai

Quick commands
- Scrape:  python recipe_scraper.py "<ALLRECIPES_URL>"   # creates recipe.json
- Parse:   python recipe_parser.py                         # writes src/parsed_recipes.json
- Run UI:  python src/pt1/main.py

Model & recommended LLM settings
- Model: gemini-2.5-flash (alternative: gemini-2.5-flash-lite)
- Temperature: 0.0 (deterministic) — raise to 0.2–0.5 for creative answers
- Max tokens (response): 512
- Top_p / nucleus sampling: 0.95
- Use system prompt in `unified_system_prompt.txt`

System architecture
- Scraper -> Parser -> Interactive assistant
  - Scraper: downloads recipe page, emits `recipe.json` (title, ingredients, steps)
  - Parser: `recipe_parser.py` + `parser_1.py` convert `recipe.json` into
    actionable, sentence-level `src/parsed_recipes.json` (ingredients, tools, times, temps, actions)
  - Assistant: `src/pt1/main.py` + `step_manager.py` provide CLI/speech interaction;
    optional LLM integration via `src/pt3/gemini_llm.py` for model-assisted answers

Components
- `recipe_scraper.py`: requests + BeautifulSoup extraction (Allrecipes print view friendly)
- `recipe.json`: scraped structured recipe (qty/unit/name + substep sentences)
- `recipe_parser.py`: orchestrates parsing of substeps -> `src/parsed_recipes.json`
- `parser_1.py`: spaCy-based rules, rapidfuzz fuzzy match, regex time/temp extraction
- `step_manager.py`: load parsed steps, provide current/next/prev helpers
- `src/pt1/main.py`: CLI glue that prints recipe, walks steps, handles queries
- `src/pt3/gemini_llm.py`: small wrapper that sends system+recipe+step+question to Gemini (requires Google GenAI client)
- Data: `culinary_dictionary.json`, `common_cooking_tools.txt`, `ingredient_substitutions.json`, `tools.txt`