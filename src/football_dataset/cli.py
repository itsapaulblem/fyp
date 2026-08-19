from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from football_dataset.manifest import build_manifest, validate_manifest
from football_dataset.pilot import compare_pilot, prepare_pilot_inputs, run_pilot


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
CONFIG_PATH = PROJECT_ROOT / "config" / "dataset.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def download_gamestate() -> None:
    from SoccerNet.Downloader import SoccerNetDownloader

    config = load_config()["sources"]["gamestate"]
    destination = RAW_ROOT / "gamestate"
    destination.mkdir(parents=True, exist_ok=True)
    downloader = SoccerNetDownloader(LocalDirectory=str(destination))
    downloader.downloadDataTask(task=config["task"], split=config["splits"])


def download_tracking() -> None:
    from SoccerNet.Downloader import SoccerNetDownloader

    config = load_config()["sources"]["tracking"]
    destination = RAW_ROOT / "tracking"
    destination.mkdir(parents=True, exist_ok=True)
    password = os.environ.get("SOCCERNET_PASSWORD")
    errors: list[str] = []

    for task in config["tasks"]:
        try:
            downloader = SoccerNetDownloader(LocalDirectory=str(destination))
            if password:
                downloader.password = password
            downloader.downloadDataTask(task=task, split=config["splits"])
            return
        except Exception as exc:  # Official SDK errors vary by backend/version.
            errors.append(f"{task}: {exc}")

    details = "\n".join(errors)
    raise RuntimeError(f"All official Tracking download variants failed:\n{details}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare the official SoccerNet coaching-evaluation sources."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    download = subparsers.add_parser("download", help="Download an official source")
    download.add_argument(
        "--source", choices=("gamestate", "tracking", "all"), required=True
    )
    subparsers.add_parser("manifest", help="Build metadata directly from the ZIPs")
    subparsers.add_parser("validate", help="Validate the generated dataset manifest")
    subparsers.add_parser(
        "pilot-prepare", help="Build the audited 16-frame pilot sampling manifest"
    )
    pilot_run = subparsers.add_parser(
        "pilot-run", help="Run Qwen on prepared pilot frame strategies"
    )
    pilot_run.add_argument(
        "--strategy",
        choices=("uniform", "event_centered", "both"),
        default="both",
    )
    pilot_run.add_argument("--limit", type=int)
    pilot_run.add_argument("--overwrite", action="store_true")
    pilot_run.add_argument("--timeout", type=int, default=900)
    subparsers.add_parser(
        "pilot-compare", help="Create a technical comparison of completed pilot runs"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "download":
        if args.source in {"gamestate", "all"}:
            download_gamestate()
        if args.source in {"tracking", "all"}:
            download_tracking()
    elif args.command == "manifest":
        print(json.dumps(build_manifest(PROJECT_ROOT), indent=2))
    elif args.command == "validate":
        print(json.dumps(validate_manifest(PROJECT_ROOT), indent=2))
    elif args.command == "pilot-prepare":
        print(json.dumps(prepare_pilot_inputs(PROJECT_ROOT), indent=2))
    elif args.command == "pilot-run":
        strategies = (
            ("uniform", "event_centered")
            if args.strategy == "both"
            else (args.strategy,)
        )
        written = run_pilot(
            PROJECT_ROOT,
            strategies,
            overwrite=args.overwrite,
            limit=args.limit,
            timeout=args.timeout,
        )
        print(json.dumps({"written": [str(path) for path in written]}, indent=2))
    elif args.command == "pilot-compare":
        print(json.dumps(compare_pilot(PROJECT_ROOT), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
