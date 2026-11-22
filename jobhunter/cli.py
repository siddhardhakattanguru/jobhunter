"""Command line entry point.

  python -m jobhunter run              fetch, score, draft material for top matches
  python -m jobhunter list [--min 70]  show tracked jobs
  python -m jobhunter mark <id> applied
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from . import db, llm, sources

OUT_DIR = Path("output")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "job"


def _load_profile() -> str:
    p = Path("profile.md")
    if not p.exists():
        sys.exit("profile.md not found. Copy profile.example.md to profile.md and fill it in.")
    return p.read_text(encoding="utf-8")


def _load_config() -> dict:
    return yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))


def cmd_run(_args) -> None:
    profile, cfg = _load_profile(), _load_config()
    OUT_DIR.mkdir(exist_ok=True)
    conn = db.connect()

    excludes = [k.lower() for k in cfg.get("exclude_title_keywords", [])]
    jobs = sources.fetch_all(cfg)
    fresh = [
        j for j in jobs
        if not db.is_known(conn, j.id)
        and not any(k in j.title.lower() for k in excludes)
    ][: cfg.get("max_jobs_per_run", 40)]
    print(f"Fetched {len(jobs)} jobs, {len(fresh)} new to score.")

    min_score = cfg.get("min_score_to_tailor", 70)
    max_tailor = cfg.get("max_tailored_per_run", 8)
    tailored = 0

    for i, j in enumerate(fresh, 1):
        print(f"[{i}/{len(fresh)}] scoring: {j.title[:45]} @ {j.company[:20]}", flush=True)
        try:
            score, reason = llm.score_job(profile, cfg.get("preferences", ""), j)
        except Exception as e:
            print(f"[warn] scoring failed for {j.title} @ {j.company}: {e}")
            continue

        notes_file = None
        if score >= min_score and tailored < max_tailor:
            try:
                body = llm.tailor(profile, j)
                path = OUT_DIR / f"{score:03d}-{_slug(j.company)}-{_slug(j.title)}-{j.id[:6]}.md"
                path.write_text(
                    f"# {j.title} @ {j.company}\n\n"
                    f"- Score: {score}\n- Location: {j.location}\n- Apply: {j.url}\n"
                    f"- Why: {reason}\n\n{body}\n",
                    encoding="utf-8",
                )
                notes_file = str(path)
                tailored += 1
            except Exception as e:
                print(f"[warn] tailoring failed for {j.title} @ {j.company}: {e}")

        db.save(conn, j, score, reason, notes_file)
        flag = "*" if notes_file else " "
        print(f"{flag} {score:3d}  {j.company[:24]:24}  {j.title[:50]}")

    print(f"\nDone. {tailored} application drafts in ./{OUT_DIR}/ - review, edit, then apply yourself.")


def cmd_list(args) -> None:
    conn = db.connect()
    rows = db.list_jobs(conn, min_score=args.min, status=args.status)
    for r in rows:
        print(f"{r['id']}  {r['score']:3d}  {r['status']:11}  {r['company'][:22]:22}  {r['title'][:45]}")
    print(f"\n{len(rows)} jobs.")


def cmd_mark(args) -> None:
    conn = db.connect()
    if db.set_status(conn, args.id, args.status):
        print(f"{args.id} -> {args.status}")
    else:
        sys.exit(f"no job with id {args.id}")


def main() -> None:
    load_dotenv()
    ap = argparse.ArgumentParser(prog="jobhunter")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run", help="fetch, score and draft").set_defaults(fn=cmd_run)

    p_list = sub.add_parser("list", help="show tracked jobs")
    p_list.add_argument("--min", type=int, default=0)
    p_list.add_argument("--status", choices=db.STATUSES)
    p_list.set_defaults(fn=cmd_list)

    p_mark = sub.add_parser("mark", help="update a job's status")
    p_mark.add_argument("id")
    p_mark.add_argument("status", choices=db.STATUSES)
    p_mark.set_defaults(fn=cmd_mark)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
