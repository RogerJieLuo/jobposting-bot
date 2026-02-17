# LinkedIn Job Crawler

Automatically crawls LinkedIn for Software Engineer jobs posted within the last hour with fewer than 100 applicants, uses Ollama to evaluate fit, and sends matches to Slack.

---

## 1. Ollama setup

- Install [Ollama](https://ollama.com) and pull a model locally (e.g. `ollama pull qwen3:8b`).
- You can set `OLLAMA_MODEL` (default: `qwen3:8b`).
- Ollama answer mode toggle:
  - `OLLAMA_WEB_SEARCH_ENABLED=0` (default): use local model (`ollama.chat`).
  - `OLLAMA_WEB_SEARCH_ENABLED=1`: use `ollama web_search` to answer the prompt.
- Optional: `OLLAMA_WEB_SEARCH_MAX_RESULTS` (default: `5`).
- If web search mode is enabled, set API key by either:
  - env var `OLLAMA_API_KEY` (recommended for GitHub Actions), or
  - file `config/ollama_api_key.txt` (one line API key).
- Prompt files live in `prompts/default/` (`profile.txt`, `evaluation_rules.txt`, `company_screening_rules.txt`, `job_evaluator.txt`); edit as needed. For per-country prompts use `prompts/<country>/`; see **Per-country config** below.

## 1.1 Gemini setup (free API)

- Create an API key in Google AI Studio.
- Set API key by either:
  - env var `GEMINI_API_KEY` (recommended for GitHub Actions), or
  - file `config/gemini_api_key.txt` (one line).
- Optional:
  - `GEMINI_MODEL` (default: `gemini-2.5-flash`)

## 1.2 Choose LLM provider

- In `main.py`, set `llm_provider = "ollama"` or `llm_provider = "gemini"`.
- You can also override with env var `LLM_PROVIDER=ollama|gemini`.
- Fallback toggle (when `LLM_PROVIDER=gemini`):
  - `ALLOW_OLLAMA_FALLBACK=1` (default): if Gemini fails, retry each job with Ollama.
  - `ALLOW_OLLAMA_FALLBACK=0`: if Gemini fails, do not retry with Ollama.
- Company screening toggle:
  - `ENABLE_COMPANY_SCREENING=1` (default): include company screening rules + company context in prompt.
  - `ENABLE_COMPANY_SCREENING=0`: use original prompt flow without company screening section.
- Provider behavior:
  - `ollama`: one request per job.
  - `gemini`: batch mode (all new jobs in one request per country), returns structured JSON per job with score/rank.

---

## 2. Slack setup

- Create a `config/` directory in the project and add a file `config/slack_webhook.txt`.
- Put your Slack Incoming Webhook URL in that file (one line, no extra spaces).
- Or set env var `SLACK_WEBHOOK_URL` (recommended for GitHub Actions).
- The notification template is at `templates/default/slack_job_template.json`; override per country with `templates/<country>/`.

## 2.1 Seen jobs storage (Supabase + fallback)

- Seen-job dedup now supports Supabase first, with local file fallback.
- Configure Supabase via env vars:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - Optional: `SUPABASE_SEEN_JOBS_TABLE` (default: `seen_jobs`)
- Or configure Supabase via files under `config/`:
  - `config/supabase_url.txt`
  - `config/supabase_service_role_key.txt`
- If Supabase env vars are missing, or Supabase read/write fails, app automatically falls back to local files under `seen_jobs/*.txt`.
- Recommended Supabase table schema:
  - `job_id` (text primary key)
  - `job_title` (text)
  - `url` (text, unique)
  - `company` (text)
  - `location` (text)
  - `update_at` (timestamptz)
  - `create_at` (timestamptz)
  - `job_description` (text)
  - `rank` (json/jsonb)

## GitHub Actions secrets

For scheduled runs in GitHub Actions, add these repository secrets:

- Required:
  - `SLACK_WEBHOOK_URL`
  - `GEMINI_API_KEY` (if using Gemini as primary provider)
  - `SUPABASE_URL` (if using Supabase dedup)
  - `SUPABASE_SERVICE_ROLE_KEY` (if using Supabase dedup)
- Required only in specific modes:
  - `OLLAMA_API_KEY` (only when `OLLAMA_WEB_SEARCH_ENABLED=1`)
- Optional runtime toggles (can be Actions env vars, usually not secrets):
  - `LLM_PROVIDER`
  - `ALLOW_OLLAMA_FALLBACK`
  - `ENABLE_COMPANY_SCREENING`
  - `GEMINI_MODEL`
  - `OLLAMA_MODEL`
  - `OLLAMA_WEB_SEARCH_ENABLED`
  - `OLLAMA_WEB_SEARCH_MAX_RESULTS`

---

## 3. Mac scheduled run (launchd)

When running the script inside a virtual environment, you can use launchd to schedule it.

1. **Create the plist**  
   - `cd ~/Library/LaunchAgents`  
   - Create `com.jobposting.plist` with `WorkingDirectory`, `ProgramArguments`, etc. pointing at your venv and `main.py`.

2. **Load the job**  
   ```bash
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.jobposting.plist
   ```  
   Verify: `launchctl list | grep jobposting` — you should see something like `-   0   com.jobposting`.

3. **Unload the job**  
   ```bash
   launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.jobposting.plist
   ```

4. **After editing the plist**  
   Unload then load again for changes to take effect.

---

## Per-country config

Different countries can use different **Ollama prompts** and **Slack message templates**:

- **Prompts:** Put `profile.txt`, `evaluation_rules.txt`, `company_screening_rules.txt`, and `job_evaluator.txt` under `prompts/<country>/`; unconfigured countries fall back to `prompts/default/`.
  - Optional basic template for screening-off mode: `job_evaluator_basic.txt`.
  - Gemini batch templates:
    - `gemini_batch_job_evaluator.txt` (company screening ON)
    - `gemini_batch_job_evaluator_basic.txt` (company screening OFF)
- **Slack template:** Use `templates/<country>/slack_job_template.json`; unconfigured countries use `templates/default/`.

In `main.py`, set `location_to_country` to map LinkedIn location strings to country keys (e.g. `"Japan": "japan"`). For example, add `prompts/japan/` and `templates/japan/slack_job_template.json` to use Japan-specific config.
