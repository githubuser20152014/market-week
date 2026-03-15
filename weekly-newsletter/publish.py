#!/usr/bin/env python3
"""Unified publish orchestrator for Framework Foundry newsletters.

Usage:
    # Daily (Mon–Fri)
    python publish.py --daybreak --date 2026-03-15

    # Weekly (Saturday)
    python publish.py --weekly --date 2026-03-15

    # Dry run (fetch + validate only, no generation or publish)
    python publish.py --daybreak --date 2026-03-15 --dry-run
    python publish.py --weekly  --date 2026-03-15 --dry-run
"""

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _step(label: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")


def _run(cmd: list[str], step_name: str) -> None:
    """Run a subprocess command; stop immediately on failure."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    if result.returncode != 0:
        print(f"\n[FAIL] Step '{step_name}' exited with code {result.returncode}.")
        print(f"  Suggestion: check the output above for the root cause, fix it, "
              f"then re-run this step.")
        sys.exit(result.returncode)


def _confirm(prompt: str) -> bool:
    """Return True if the user answers y/yes."""
    try:
        answer = input(f"\n{prompt} [y/n]: ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def _print_summary(title: str, resolutions: list[str], flagged: list[str],
                   outputs: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  SUMMARY — {title}")
    print(f"{'='*60}")
    if resolutions:
        print("  Auto-resolved:")
        for r in resolutions:
            print(f"    · {r}")
    if flagged:
        print("  Flagged for review:")
        for f in flagged:
            print(f"    ! {f}")
    if outputs:
        print("  Outputs:")
        for o in outputs:
            print(f"    → {o}")
    print()


# ---------------------------------------------------------------------------
# Resolution log parser
# ---------------------------------------------------------------------------

def _parse_resolution_log(date_str: str) -> tuple[list[str], list[str]]:
    """Return (auto_resolved, flagged) lists from the audit log."""
    log_path = BASE_DIR / "output" / f"price_resolution_{date_str}.txt"
    if not log_path.exists():
        return [], []

    resolved = []
    flagged  = []
    for line in log_path.read_text().splitlines():
        if "auto-resolved" in line:
            resolved.append(line.strip())
        elif "FAIL" in line:
            flagged.append(line.strip())
    return resolved, flagged


# ---------------------------------------------------------------------------
# Daybreak flow (Mon–Fri)
# ---------------------------------------------------------------------------

def run_daybreak(date_str: str, dry_run: bool) -> None:
    _step(f"Daybreak publish — {date_str}")

    # Step 1: Fetch + verify live data
    _step("1/5  Fetch + verify daybreak data")
    if not dry_run:
        _run(
            [sys.executable, "generate_market_day_break.py",
             "--date", date_str, "--live", "--verify"],
            "fetch-verify-daybreak",
        )
    else:
        print("  [dry-run] Would fetch + verify live daybreak data.")

    if dry_run:
        print("\n[dry-run] Stopping here — no generation or publish steps.")
        return

    # Step 2: Build combined site
    _step("2/5  Build combined site")
    _run([sys.executable, "build_combined_site.py"], "build-site")

    # Step 3: Generate PDF (if not already generated with --live)
    # Note: generate_market_day_break.py --live already handles PDF via --pdf flag.
    # build_combined_site.py re-renders PDFs as needed. No extra step needed here.

    # Step 4: Commit + email via publish_daybreak.sh
    _step("3/5  Commit, push, and email via publish_daybreak.sh")
    _run(
        ["bash", "publish_daybreak.sh", date_str, "--publish"],
        "publish-daybreak-sh",
    )

    # Step 5: Summary
    resolved, flagged = _parse_resolution_log(date_str)
    outputs = [
        str(BASE_DIR / "output" / f"market_day_break_{date_str}.md"),
        str(BASE_DIR / "output" / f"market_day_break_{date_str}.pdf"),
        str(BASE_DIR / "output" / f"price_resolution_{date_str}.txt"),
    ]
    _print_summary(f"Daybreak {date_str}", resolved, flagged, outputs)


# ---------------------------------------------------------------------------
# Weekly flow (Saturday)
# ---------------------------------------------------------------------------

def run_weekly(date_str: str, dry_run: bool) -> None:
    _step(f"Weekly newsletter publish — {date_str}")

    # Step 1: Fetch market prices + econ calendar (live)
    _step("1/7  Fetch live data (prices + econ calendar)")
    if not dry_run:
        # Prices are fetched during generation; econ calendar is wired into
        # fetch_data.py when --live is passed. Run a preflight to check the
        # econ calendar fetch independently before generation.
        from data.fetch_econ_calendar import fetch_econ_calendar_with_fallback
        print(f"  Prefetching econ calendar for {date_str} ...")
        try:
            fetch_econ_calendar_with_fallback(date_str)
        except Exception as e:
            print(f"  WARNING: Econ calendar prefetch failed ({e}). "
                  "Generation will attempt its own fallback.")
    else:
        print("  [dry-run] Would prefetch econ calendar.")

    # Step 2: Smart price resolver — run via weekly generator with --verify
    _step("2/7  Fetch live prices + verify")
    if not dry_run:
        # generate_newsletter.py --live auto-enables --verify unless --no-verify is passed
        _run(
            [sys.executable, "generate_newsletter.py",
             "--date", date_str, "--live", "--pdf"],
            "generate-us-newsletter",
        )
    else:
        print("  [dry-run] Would run generate_newsletter.py --live --pdf")

    if dry_run:
        print("\n[dry-run] Stopping here — no further generation or publish steps.")
        return

    # Step 3: Generate international newsletter
    _step("3/7  Generate international newsletter")
    _run(
        [sys.executable, "generate_intl_newsletter.py",
         "--date", date_str, "--live", "--pdf"],
        "generate-intl-newsletter",
    )

    # Step 4: Build combined site
    _step("4/7  Build combined site")
    _run([sys.executable, "build_combined_site.py"], "build-site")

    # Step 5: Summary of auto-resolutions and flagged items
    resolved, flagged = _parse_resolution_log(date_str)
    outputs = [
        str(BASE_DIR / "output" / f"newsletter_{date_str}.md"),
        str(BASE_DIR / "output" / f"newsletter_{date_str}.pdf"),
        str(BASE_DIR / "output" / f"intl_newsletter_{date_str}.pdf"),
        str(BASE_DIR / "output" / f"price_resolution_{date_str}.txt"),
        str(BASE_DIR / "site" / "index.html"),
    ]
    _print_summary(f"Weekly {date_str}", resolved, flagged, outputs)

    # Step 6: Confirm before committing
    _step("5/7  Review + commit")
    if flagged:
        print("  WARNING: There are flagged price items above. Review before committing.")

    if not _confirm("Ready to commit and push to GitHub?"):
        print("  Skipping commit. Run manually when ready:")
        print(f"    git add weekly-newsletter/")
        print(f"    git commit -m 'Publish weekly newsletter — {date_str}'")
        print(f"    git push origin master")
        return

    # Step 7: Commit and push
    _step("6/7  Commit and push")
    _run_git_commit(date_str)


def _run_git_commit(date_str: str) -> None:
    """Stage weekly output files and commit."""
    repo_root = BASE_DIR.parent
    wn = "weekly-newsletter"

    files_to_stage = [
        f"{wn}/fixtures/indices_{date_str}.json",
        f"{wn}/fixtures/econ_calendar_{date_str}.json",
        f"{wn}/fixtures/intl_indices_{date_str}.json",
        f"{wn}/fixtures/intl_econ_calendar_{date_str}.json",
        f"{wn}/output/newsletter_{date_str}.md",
        f"{wn}/output/newsletter_{date_str}.pdf",
        f"{wn}/output/intl_newsletter_{date_str}.pdf",
        f"{wn}/output/price_resolution_{date_str}.txt",
        f"{wn}/site/",
    ]

    for f in files_to_stage:
        full = repo_root / f
        # Only stage if the path exists
        if Path(full).exists() or str(f).endswith("/"):
            subprocess.run(
                ["git", "add", str(f)],
                cwd=str(repo_root),
            )

    msg = f"Publish weekly newsletter — {date_str}"
    result = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=str(repo_root),
    )
    if result.returncode != 0:
        print("  Nothing to commit or commit failed.")
        return

    push = subprocess.run(["git", "push", "origin", "master"], cwd=str(repo_root))
    if push.returncode != 0:
        print("[FAIL] git push failed. Check remote status and push manually.")
        sys.exit(push.returncode)

    print(f"\n  Committed and pushed: {msg}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified publish orchestrator for Framework Foundry newsletters."
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--daybreak",
        action="store_true",
        help="Run the daily Market Day Break publish flow (Mon–Fri).",
    )
    mode.add_argument(
        "--weekly",
        action="store_true",
        help="Run the weekly newsletter publish flow (Saturday).",
    )

    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Publish date YYYY-MM-DD (default: today).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate only; skip generation and publish steps.",
    )

    args = parser.parse_args()

    if args.daybreak:
        run_daybreak(args.date, dry_run=args.dry_run)
    else:
        run_weekly(args.date, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
