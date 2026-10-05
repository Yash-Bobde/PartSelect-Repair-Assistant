# Checkpoint: PartSelect case study (updated 2026-10-04, after the price refresh and interview-day fixes)

Instalily PartSelect chat-agent case study, prepared for a mock interview (original build: ~4 hours).
GitHub: private repo `Yash-Bobde/PartSelect` (personal account). `partselect-backend/.env` is git-ignored and never committed; `.env.example` holds only a placeholder key.

## Status

- `main` on GitHub has everything below: the 2026-10-03 bug-fix pass, the 2026-10-04 price refresh (branch `refresh-partselect-prices`) and the interview-day fixes (branch `interview-day-fixes`).
- A fresh clone installs and runs on Windows by following the README, including when Claude runs the commands (output piped, not a console). Tested on 2026-10-04 from a fresh clone: `pip install -r requirements.txt`, `init.sql` + loader into an empty database, backend, frontend build, and the brief's questions.
- Interview prep (PDF + PowerPoint) is kept locally in `Downloads/roseVZ-PartSelect/Interview-Prep/`, outside the repo.

## Run it locally (Windows)

1. Open Docker Desktop, then `cd partselect-backend` and `docker compose up -d` (Postgres :5432, Redis :6379, ChromaDB :8001).
2. First time only:
   - `py -3.12 -m venv venv` (the pinned numpy/scipy need Python ≤ 3.12)
   - `.\venv\Scripts\python.exe -m pip install -r requirements.txt` (installs as-is; `uvloop` is skipped on Windows, and the scraper packages live in `scraper/requirements.txt`)
   - `copy .env.example .env`, then set `DEEPSEEK_API_KEY` to the OpenAI key (`DEEPSEEK_BASE_URL=https://api.openai.com/v1`, `DEEPSEEK_MODEL=gpt-4o-mini`).
   - `.\venv\Scripts\python.exe scripts\load_to_database.py`: 321 parts, 321 install guides, 49 troubleshooting entries, 3 compatibility rows, 830 ChromaDB docs. Safe to re-run; it updates in place.
3. Backend: `.\venv\Scripts\python.exe -m app.main` from `partselect-backend` (http://localhost:8000). Restart it after editing `.env` or re-running the loader (the loader recreates the ChromaDB collection; a running backend keeps the old one and symptom questions fail with "Collection … does not exist").
4. Frontend: `cd frontend`, `npm install`, `npm start` (http://localhost:3000).

Stop the backend with Ctrl+C in its terminal. It runs in uvicorn reload mode, so killing only the parent process leaves a worker serving port 8000 with stale state. On Windows the auto-reload is also unreliable (it logged "Reloading..." but kept the old worker serving), so restart the backend by hand after any code change.

## Price refresh (2026-10-04)

PartSelect now sits behind a Cloudflare check: plain requests, headless Chrome and the original Selenium scrapers all get "Just a moment…". `scraper/refresh_parts.py` re-scrapes the 321 product pages already in the catalog with `undetected-chromedriver` (visible Chrome, no clicks needed) and parses the current page layout (`div#main` data attributes). About an hour with 3–8 s pauses; progress is cached in `scraper/scraped_data/` (git-ignored), so an interrupted run resumes.

- 535 of 550 records had a new price (e.g. the ice maker PS11738120 went from $80.20 to $77.34).
- Install difficulty/time now come from PartSelect's customer ratings instead of pipeline defaults.
- 11 parts previously dropped for a missing price are back (310 → 321).
- To refresh again: install `scraper/requirements.txt`, run `refresh_parts.py`, then `process_all_data.py` and `load_to_database.py`, then restart the backend.

## Bugs fixed on 2026-10-03 (found by running the app)

1. **Conversation state grew exponentially.** `messages` used an `operator.add` reducer while every node returns the full state, so the list doubled at each node: 34 → 562 → 9,010 → 288,354 stored messages (43.7 MB in Redis) after 4 turns. Fix: plain channel (`app/agent/state.py:18`). Now exactly 2 messages per turn.
2. **A part number "stuck" for the whole conversation.** After "Tell me about PS11701542", "My dishwasher is not draining" recommended that fridge water filter. Fix: the remembered part is looked up only for details/install/compatibility intents, or when it appears in the message (`nodes.py:25`, `nodes.py:159`).
3. **An unknown part showed a different part.** "Tell me about PS99999999" displayed the previous part's details. Fix: per-turn results are cleared at the start of each turn (`nodes.py:64`).
4. **Wrong compatibility for the brief's example.** `init.sql` seeded a fake "Ice Maker Assembly" for PS11752778 (really a fridge door shelf bin) and rows saying it fits dishwasher models (100%). Its real specs were also never loaded, because the upsert skipped `specifications`. Fixes:
   - seed rows removed from `init.sql`
   - the loader upsert now updates every column
   - the loader is now re-runnable without duplicating guides or troubleshooting entries
   - a new appliance check (`_MODEL_APPLIANCE`, `nodes.py:924`, used at `:852`) answers "No" for a fridge part vs a dishwasher model, where brand-family matching alone said "likely fits". The UI shows a "Doesn't fit" card.
5. **Invented install facts.** The scraper got "N/A" for difficulty and time on all 550 records, and the pipeline defaults them (moderate, 30 min, `["screwdriver"]`). The UI no longer shows them (`InstallCard.js`, `PartDetail.js`).
6. **Search on `None`.** `chat.py` seeds `search_query=None`, so a `.get()` default never applied. Fix: `or` fallback to the user's message (`nodes.py:140`).

## Fixed on 2026-10-04 (interview-day fixes)

7. **"My Whirlpool ice maker is not making ice" was declined as off-topic.** Without the word "fridge", the classifier set `appliance_type = "ice maker"` and the scope guard (`nodes.py:467`) refused it. Fix: `_normalize_appliance` (`nodes.py:51`, applied at `:109`) maps ice maker / freezer / water dispenser to "refrigerator".
8. **A fresh install failed or was wrong:**
   - `pip install -r requirements.txt` failed on Windows (`uvloop`) and on a `selenium`/`urllib3` conflict. `uvloop` now has a non-Windows marker; the scraper packages moved to `scraper/requirements.txt`.
   - Nothing ran `seed_compatibility.sql`; the loader now applies it.
   - On Windows, piped output (e.g. when Claude runs the commands) falls back to cp1252, so the loader, `process_all_data.py` and even the backend's startup message crashed on emoji. The entry points now switch stdout/stderr to UTF-8.
9. **Scraper bugs:** both scrapers had `brand_links = brand_links[10]` (now `[:max_brands]`); `dishwasher_scraper.py` targeted the refrigerator URL.
10. **A branded search with no exact brand match said "couldn't find any parts".** "Samsung dishwasher spray arms" found 12 spray arms (none Samsung) and filtered them all out. Common searches hit this for most brands (KitchenAid, Maytag and Kenmore parts are all recorded as Whirlpool). Now the brand filter keeps the other brands' parts when there's no match (`nodes.py:276`), and the reply says they're other brands that may not fit and asks for the model number (`_generate_search_response`). The reply still has the "Here are the parts I found:" line the frontend cuts at, so the UI shows the note above the part cards. With a brand match, results are unchanged.

Verified working after the fixes: the brief's compatibility example → No; seeded filter → Yes 97%; ice maker questions with or without "fridge"; drain pump diagnosis; new prices in API and UI.

## Still open (known issues; fix only with approval)

1. **ChromaDB results are unused.** `recommend_parts` reads `relevant_docs` (`nodes.py:320`) but never puts them in the LLM context, although the README advertises hybrid retrieval.
2. **Diagnosis replies don't flag other brands.** Diagnosis searches don't filter by brand (ranking floats the brand first), so "My Samsung dishwasher is not draining" can list other brands' pumps without the "may not fit" note that part searches now give.
3. **`symptoms` is always empty in the API**, because the agent fills `symptom`. The appliance type also stays unknown during part-number questions.
4. **Install details are hidden in the UI.** Real difficulty/time now exist for most parts (from the 2026-10-04 refresh), but parts without a rating still get the pipeline defaults (`process_installation_guides` in `process_all_data.py`), and the backend templates state them. The UI hides them all.
5. **A wasted LLM call.** Ranking runs even for a single looked-up part.
6. **Redis URL hardcoded** in `chat.py:39`.
7. **The original brand-crawl scrapers are outdated.** Their selectors target the old page layout and they get stopped by Cloudflare; use `refresh_parts.py` instead.
8. **Troubleshooting doc IDs aren't reproducible.** `process_all_data.py` builds `chromadb_doc_id` from Python's randomized `hash()`, so they change on every run.
9. **Dead code:** `_generate_llm_response`, `extract_model_or_part`, `search_products_by_symptom`, `get_troubleshooting_info`, `generate_with_chat_history`, the `conversations` table.

## Next steps

- Re-run the brief's questions in one conversation after any change (about 2 `gpt-4o-mini` calls each).
