# Checkpoint: PartSelect case study (2026-09-28)

Instalily PartSelect chat-agent case study, prepared for a mock interview.
GitHub: private repo `Yash-Bobde/PartSelect` (personal account). `partselect-backend/.env` is git-ignored and never committed.

## Status

- Runs locally end to end: Docker services, FastAPI backend, React frontend.
- Frontend redesigned and verified (light/dark, desktop and side-panel widths, all intents).
- **Backend code is unchanged.** The owner asked for it not to be edited; the problems below are still open.

## Run it locally (Windows)

1. Open Docker Desktop, then `cd partselect-backend` and `docker compose up -d` (Postgres :5432, Redis :6379, ChromaDB :8001).
2. First time only:
   - `py -3.12 -m venv venv` (the pinned numpy/scipy need Python ≤ 3.12)
   - install `requirements.txt` **without** `uvloop` (no Windows support) and `selenium` / `undetected-chromedriver` (scraper-only; selenium 4.36 conflicts with the pinned `urllib3==2.3.0`)
   - `.\venv\Scripts\python.exe scripts\load_to_database.py` (311 parts, 233 install guides, 43 troubleshooting entries, 720 ChromaDB docs)
3. `partselect-backend/.env` (not in git):
   ```
   DEEPSEEK_API_KEY=<OpenAI key>
   DEEPSEEK_BASE_URL=https://api.openai.com/v1
   DEEPSEEK_MODEL=gpt-4o-mini
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/partselect
   REDIS_URL=redis://localhost:6379/0
   CHROMA_HOST=localhost
   CHROMA_PORT=8001
   CORS_ORIGINS=["http://localhost:3000","http://localhost:3002","http://localhost:5173"]
   ```
   The client only speaks the OpenAI chat-completions format, so the `DEEPSEEK_*` names work with an OpenAI key.
4. Backend: `cd partselect-backend` then `.\venv\Scripts\python.exe -m app.main` (http://localhost:8000). Restart it after editing `.env`.
5. Frontend: `cd frontend`, `npm install`, `npm start` (http://localhost:3000).

The GAF project also uses ports 3000 and 8000; stop it first.

## Frontend redesign (done)

- PartSelect's live palette (cream `#efe9d2`, ink `#12130f`, orange `#ee9721`, arctic denim `#d4ebed`) and Titillium Web.
- Repair workspace: chat on the left, "Your repair" panel on the right (appliance, brand, model, reported problem, parts shortlist with total). Below 1100px the panel becomes a drawer.
- Welcome screen with appliance picker and the brief's example questions.
- Per-intent views: part cards (install-video thumbnail as the image), part detail, installation guide (inline YouTube + checklist), compatibility verdict.
- "How I answered" trace: LangGraph path (`understand → search → gather_context → recommend → respond`) plus what the agent understood.
- Markdown sanitised with DOMPurify; icons from lucide-react; motion via framer-motion (respects reduced motion).
- Code: `frontend/src/{components,hooks,lib,context,styles}`.

## Backend problems (open; fix only with approval)

Ordered by how visible they are in a demo.

1. **AI ranking never takes effect.** `app/agent/nodes.py:323` runs `json.loads` on the raw LLM reply and the bare `except` at `:338` falls back to search order. Every reply shows the fallback line "Here are the most relevant parts based on your search.", and a GE ice maker ranked first for a Whirlpool question. Likely cause (not verified): the model wraps its JSON in ``` fences. Fix: use `llm.generate_json()` (`app/core/llm.py` strips fences) and log parse failures.
2. **Brand isn't remembered.** "My Whirlpool fridge…" came back with `metadata.brand = null`. Cause not verified; the classifier's example JSON in `app/agent/intent.py` only shows `appliance_type` and `search_query`.
3. **Ordinary words taken as model numbers.** "Is PS11701542 compatible with my fridge?" set `model_number = "fridge"`, and the reply said it "should be compatible with your fridge". Fix: validate extracted model numbers (letters plus digits, 5+ chars). `extract_model_or_part` (`intent.py:379`) exists but isn't used for this.
4. **Diagnosis ignores the brand.** The brand filter only runs for search/details/installation (`nodes.py:218`).
5. **ChromaDB results are unused.** `gather_context` stores `relevant_docs` (`nodes.py:253`) but `recommend_parts` never sends them to the LLM.
6. **Compatibility is mostly guesswork.** The `compatibility` table (`tools.py:223`) is never loaded. `_is_universal_part` (`nodes.py:779`) calls a filter compatible if it has more than 5 replacements or the model starts with the brand's letter.
7. **Off-topic questions aren't declined.** `_generate_general_response` (`nodes.py:840`) uses a generic prompt; the brief asks the agent to stay in scope.
8. **`symptoms` is always empty.** The API returns `symptoms` (`app/api/chat.py:164`) but the agent stores `symptom`. The frontend works around it by listing the user's diagnosis messages.
9. Minor: Redis URL hardcoded in `chat.py:39` (ignores `REDIS_URL`); the `requirements.txt` conflicts above; README names a `partselect-frontend` folder and a `.env.example`, and neither exists.

## Next steps

- Ask the owner before any backend change; items 1–3 have the biggest demo impact.
- After backend fixes, re-run the welcome-screen questions (about 2 `gpt-4o-mini` calls each).
