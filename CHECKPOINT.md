# Checkpoint: PartSelect case study (updated 2026-10-03)

Instalily PartSelect chat-agent case study, prepared for a mock interview.
GitHub: private repo `Yash-Bobde/PartSelect` (personal account). `partselect-backend/.env` is git-ignored and never committed; `.env.example` holds only a placeholder key.

## Status

- `main` is at `10e1515` (2026-09-30). `improved-partselect` points at the same commit, so it is fully merged (no PR; pushed directly).
- Commit `63748a5` fixed most of the backend problems from the first checkpoint (see below). Those fixes were checked by reading the code, **not** by running the app afterwards.
- Frontend redesign is done and verified (light/dark, desktop and side-panel widths, all intents); `63748a5` and `10e1515` added polish (shortlist is now memory-only).
- Backend changes still need the owner's approval.

## Run it locally (Windows)

1. Open Docker Desktop, then `cd partselect-backend` and `docker compose up -d` (Postgres :5432, Redis :6379, ChromaDB :8001).
2. First time only:
   - `py -3.12 -m venv venv` (the pinned numpy/scipy need Python ≤ 3.12)
   - install `requirements.txt` **without** `uvloop` (no Windows support) and `selenium` / `undetected-chromedriver` (scraper-only; selenium 4.36 conflicts with the pinned `urllib3==2.3.0`). A plain `pip install -r requirements.txt`, as the README says, fails.
   - `.\venv\Scripts\python.exe scripts\load_to_database.py` (311 parts, 233 install guides, 43 troubleshooting entries, 720 ChromaDB docs)
   - `Get-Content scripts\seed_compatibility.sql | docker exec -i partselect_postgres psql -U postgres -d partselect` (compatibility rows for the brief's examples; nothing runs it automatically)
3. `copy .env.example .env`, then set `DEEPSEEK_API_KEY` to the OpenAI key. The client speaks the OpenAI chat-completions format, so the `DEEPSEEK_*` names work with `DEEPSEEK_BASE_URL=https://api.openai.com/v1` and `DEEPSEEK_MODEL=gpt-4o-mini`.
4. Backend: `.\venv\Scripts\python.exe -m app.main` from `partselect-backend` (http://localhost:8000). Restart it after editing `.env`.
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

## Backend problems

### Fixed in `63748a5`

1. **AI ranking** now parses through `llm.generate_json()` (`nodes.py:348`) and floats the customer's brand to the top. Before, a GE ice maker led a Whirlpool question.
2. **Brand memory:** `brand` and `symptom` are now `AgentState` channels (`state.py:22-24`), and the classifier is told to extract brands (`intent.py:290`).
3. **Model-number validation:** `_is_valid_model` (`nodes.py:29`) rejects words like "fridge".
4. **Off-topic questions** are declined: an appliance allowlist in `generate_response` (`nodes.py:433`) plus a scoped prompt in `_generate_general_response` (`nodes.py:925`).
5. **Compatibility (partly):** brand-family logic (`nodes.py:864`) instead of "any filter fits", plus seed rows for the brief's pairs (see open item 3).
6. **LLM retries:** transient API errors retry with backoff (`app/core/llm.py:97`).
7. **README** rewritten with accurate setup; `.env.example` added.

### Still open (fix only with approval)

1. **ChromaDB results are unused.** `recommend_parts` reads `relevant_docs` (`nodes.py:291`) but never puts them in the LLM context.
2. **Diagnosis search ignores the brand.** The brand filter only runs for search/details/installation (`nodes.py:245`). Mitigated: ranking now puts the customer's brand first.
3. **Compatibility seed isn't wired up.** `scripts/seed_compatibility.sql` isn't run by the loader, Docker or the README, so the brief's pairs only get confident verdicts after running it by hand (step 2 above).
4. **`symptoms` is always empty.** The API returns `symptoms` (`app/api/chat.py:164`), but the agent only fills `symptom`. The frontend works around it.
5. **Setup rough edges:** Redis URL hardcoded in `chat.py:39` (ignores `REDIS_URL`), and `requirements.txt` can't install as-is (selenium/urllib3 conflict; uvloop on Windows), which the README's `pip install -r requirements.txt` step runs into.

## Next steps

- Re-test the welcome-screen questions against the new backend (about 2 `gpt-4o-mini` calls each), after running the compatibility seed.
- Ask the owner before fixing the open items; open item 3 and the `requirements.txt` step matter most for someone cloning the repo.
