# jobhunter

A small, human-in-the-loop job-search agent. It:

1. Pulls jobs from public APIs (Remotive for remote roles, Adzuna for India/Pune).
2. Uses an LLM (Gemini by default, Claude optional) to score each job (0-100)
   against your profile and preferences.
3. For strong matches, drafts a tailored resume-bullet list, a short cover note,
   and a list of gaps. Output lands in `output/` as Markdown.
4. Tracks everything in a local SQLite file so you never see the same job twice.

**You review and click Apply yourself.** That is deliberate:

- LinkedIn, Naukri and most job boards forbid automated applying; accounts get
  banned.
- Blind mass-applying has a low response rate. Ten targeted applications with a
  referral beat a hundred blind ones.
- The prompts only allow facts from your `profile.md`. Anything missing becomes a
  `[FILL]` placeholder, so the tool never invents experience for you.

## Setup

```bash
git clone <your-repo-url> jobhunter && cd jobhunter
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # add GEMINI_API_KEY (and optional Adzuna keys)
cp profile.example.md profile.md     # fill in with real facts
# edit config.yaml: queries, locations, exclusions, score threshold
```

### API keys

- **Gemini (default, has a free tier):** create a key in Google AI Studio and put it
  in `.env` as `GEMINI_API_KEY=...`. Free-tier limits and model availability vary;
  if the default model is not available to you, set `GEMINI_MODEL` in `.env`.
- **Claude (optional, paid):** `pip install anthropic`, then set
  `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...` in `.env`.
- **Adzuna (optional, free):** keys from developer.adzuna.com add India/Pune
  search. Without them only Remotive (remote jobs) is searched.

Free tiers may let the provider use your prompts to improve their products. Your
`profile.md` is sent with every request, so read the provider's terms and leave
out anything you would not want shared (phone, address, ID numbers).

## Use

```bash
python -m jobhunter run                  # fetch, score, draft
python -m jobhunter list --min 70        # best matches
python -m jobhunter mark <job-id> applied
```

Status values: new, shortlisted, applied, interview, offer, rejected, skipped.

Typical loop: run once a day, open the top drafts in `output/`, edit them, apply
on the company site, then `mark` the job.

## Cost control

Each job costs one small scoring call; only matches above `min_score_to_tailor`
get a longer drafting call. `max_jobs_per_run` and `max_tailored_per_run` in
`config.yaml` cap spend per run.

## Privacy

`.gitignore` excludes `.env`, `profile.md`, `jobs.db` and `output/`. Keep the
GitHub repo **private** anyway; your resume details are personal data.

## Ideas to extend

- Add sources: company career-page RSS/JSON feeds, Greenhouse/Lever public
  job-board APIs (many companies expose these).
- Email or Telegram digest of the day's top matches.
- Run on a schedule with cron or GitHub Actions (store secrets as Actions secrets).
- Playwright helper that opens the apply page and pre-fills fields, stopping
  before submit so you confirm each one.
