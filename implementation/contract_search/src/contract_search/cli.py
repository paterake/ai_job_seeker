"""Thin entry point: `contract-search run`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ai_job_seeker.ingest import load_search_config

from contract_search import config as cfg_mod
from contract_search.apify_source import DEFAULT_APIFY_CFG, load_apify_config
from contract_search.run import run_search, write_outputs


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="contract-search", description="Contract-role search and shortlist.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Ingest live listings, score them, write the shortlist")
    r.add_argument("--profile", default=None, help="Candidate profile YAML (default: the only YAML in config/profile/)")
    r.add_argument("--search-config", default=str(cfg_mod.DEFAULT_SEARCH_CFG))
    r.add_argument("--scoring-config", default=str(cfg_mod.DEFAULT_SCORING_CFG))
    r.add_argument("--output-dir", default=str(cfg_mod.DEFAULT_OUTPUT_DIR))
    r.add_argument("--apify-config", default=str(DEFAULT_APIFY_CFG))
    r.add_argument("--apify", action="store_true", help="Also query the Apify actors in apify.yaml (uses Apify credit)")
    r.add_argument("--top", type=int, default=25)
    r.add_argument("--dry-run", action="store_true", help="Synthetic listings, no API calls or keys")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = cfg_mod.load_profile(args.profile or cfg_mod.default_profile_path())
        policy = cfg_mod.load_scoring(args.scoring_config)
        ingest_cfg = load_search_config(args.search_config)
        result = run_search(ingest_cfg, profile, policy, dry_run=args.dry_run, top=args.top,
                            apify=load_apify_config(args.apify_config) if args.apify else None)
    except (cfg_mod.ConfigError, ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    md, js = write_outputs(result, profile, Path(args.output_dir))
    print(f"Fetched {result.fetched}; kept {len(result.shortlist)}; dropped {result.drops or 'none'}")
    for name, reason in result.skips:
        print(f"SKIP {name}: {reason}")
    print(f"Wrote {md}\nWrote {js}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
