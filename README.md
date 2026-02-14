# LinkedIn Job Crawler

Automatically crawls LinkedIn for Software Engineer jobs posted within the last hour with fewer than 100 applicants, uses Ollama to evaluate fit, and sends matches to Slack.

---

## 1. Ollama setup

- Install [Ollama](https://ollama.com) and pull a model locally (e.g. `ollama pull qwen3:8b`).
- In `llm/ask_ollama.py`, set `model=` to the model name you use.
- Prompt files live in `prompts/default/` (`profile.txt`, `evaluation_rules.txt`, `job_evaluator.txt`); edit as needed. For per-country prompts use `prompts/<country>/`; see **Per-country config** below.

---

## 2. Slack setup

- Create a `config/` directory in the project and add a file `config/slack_webhook.txt`.
- Put your Slack Incoming Webhook URL in that file (one line, no extra spaces).
- The notification template is at `templates/default/slack_job_template.json`; override per country with `templates/<country>/`.

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

- **Prompts:** Put `profile.txt`, `evaluation_rules.txt`, and `job_evaluator.txt` under `prompts/<country>/`; unconfigured countries fall back to `prompts/default/`.
- **Slack template:** Use `templates/<country>/slack_job_template.json`; unconfigured countries use `templates/default/`.

In `main.py`, set `location_to_country` to map LinkedIn location strings to country keys (e.g. `"Japan": "japan"`). For example, add `prompts/japan/` and `templates/japan/slack_job_template.json` to use Japan-specific config.
