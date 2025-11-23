#!/usr/bin/env python3
"""CLI wrapper for Development/installer.py"""
import argparse
from installer import run

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--aurora", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    def log(msg):
        print(msg, end='')

    def prog(pct):
        if pct == -1:
            print("[progress] indeterminate")
        else:
            print(f"[progress] {pct}%")

    rc = run(args.aurora, args.repo, force=args.force, dry_run=args.dry_run, debug=args.debug, progress=prog, log=log)
    raise SystemExit(rc)

if __name__ == "__main__":
    main()