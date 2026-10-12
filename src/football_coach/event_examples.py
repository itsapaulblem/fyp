"""Freeze annotation candidates for a new, match-disjoint in-context experiment.

This never calls a model or downloads footage. An annotation selection is not
a reviewed image dataset: the media and visibility gates remain explicit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/in_context_event_examples_v1.json"
ROLES = ("example", "development", "held_out_test")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def rank(seed: str, value: str) -> str:
    return digest(f"{seed}:{value}".encode())


def match_key(path: str) -> str:
    # Ignore provider league folders and broadcast start times; keep match date,
    # team pairing and score together when the same fixture has multiple paths.
    name = unicodedata.normalize("NFKC", path.split("/")[-1]).casefold()
    name = re.sub(r"^(\d{4}-\d{2}-\d{2})\s*-\s*\d{2}-\d{2}\s+", r"\1 ", name)
    return " ".join(name.split())


def group_roles(games: list[str], config: dict, pool: list[dict] | None = None) -> dict[str, str]:
    keys = sorted({match_key(g) for g in games}, key=lambda k: rank(config["seed"], k))
    first = int(len(keys) * config["match_split"]["example"])
    second = first + int(len(keys) * config["match_split"]["development"])
    capacities = {"example": first, "development": second - first,
                  "held_out_test": len(keys) - second}
    result = {}
    if pool is not None:
        class_matches = {
            category: {r["match_group"] for r in pool if r["class"] == category}
            for category in config["classes"]
        }
        rarest = min(class_matches, key=lambda category: (len(class_matches[category]), category))
        rare_keys = [key for key in keys if key in class_matches[rarest]]
        offset = 0
        for role in ROLES:
            minimum = (config["primary_clips_per_class"][role]
                       + config["maximum_reserves_per_class_per_role"])
            if minimum > capacities[role] or offset + minimum > len(rare_keys):
                raise ValueError("Insufficient rare-event matches for primary and reserve quotas")
            result.update({key: role for key in rare_keys[offset:offset + minimum]})
            offset += minimum
    # Fill remaining capacity in fixed hash order. The labels define strata;
    # all clips and broadcasts in a match still inherit one shared role.
    unassigned = iter(key for key in keys if key not in result)
    for role in ROLES:
        remaining = capacities[role] - sum(value == role for value in result.values())
        for _ in range(remaining):
            result[next(unassigned)] = role
    return result


def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "football-coach/0.4"})
            with urllib.request.urlopen(request, timeout=40) as response:
                return response.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Unreachable fetch state")


def annotation_url(config: dict, game: str) -> str:
    source = config["source"]
    path = urllib.parse.quote(game + "/Labels-v2.json", safe="/")
    return (
        f"https://huggingface.co/datasets/{source['labels_repository']}/resolve/"
        f"{source['labels_revision']}/{path}"
    )


def read_sources(config: dict, allow_fetch: bool) -> tuple[list[str], list[dict], dict]:
    cache = ROOT / config["workspace"] / "source_cache"
    train_path = cache / "official_train_games.json"
    if not train_path.exists():
        if not allow_fetch:
            raise ValueError("Source cache missing; use freeze --fetch-public-labels")
        cache.mkdir(parents=True, exist_ok=True)
        train_path.write_bytes(fetch(config["source"]["train_list_url"]))
    listing = json.loads(train_path.read_bytes())
    games = sorted(
        f"{league}/{season}/{game}"
        for league, seasons in listing.items()
        for season, names in seasons.items()
        for game in names
    )
    if len(games) != 300 or len(games) != len(set(games)):
        raise ValueError("Expected 300 distinct official SoccerNet-v2 train matches")

    def load(game: str) -> tuple[str, dict, dict]:
        path = cache / "labels" / f"{digest(game.encode())}.json"
        if not path.exists():
            if not allow_fetch:
                raise ValueError(f"Missing cached annotations for {game}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fetch(annotation_url(config, game)))
        raw = path.read_bytes()
        document = json.loads(raw)
        if str(document.get("UrlLocal", "")).replace("\\", "/").rstrip("/") != game:
            raise ValueError(f"Annotation identity mismatch for {game}")
        return game, document, {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(raw)}

    labels, provenance = {}, {
        train_path.relative_to(ROOT).as_posix(): digest(train_path.read_bytes())
    }
    with ThreadPoolExecutor(max_workers=8) as executor:
        pending = [executor.submit(load, game) for game in games]
        for i, future in enumerate(as_completed(pending), 1):
            game, document, record = future.result()
            labels[game] = document
            provenance[record["path"]] = record["sha256"]
            if i % 50 == 0:
                print(f"Read {i}/{len(games)} public train annotation files", flush=True)
    return games, [{"match": game, "data": labels[game]} for game in games], provenance


def candidates(documents: list[dict], config: dict) -> list[dict]:
    classes = {label: name for name, labels in config["classes"].items() for label in labels}
    before = config["clip_window"]["seconds_before_annotation"] * 1000
    after = config["clip_window"]["seconds_after_annotation"] * 1000
    result = []
    seen = set()
    for document in documents:
        game = document["match"]
        for annotation in document["data"]["annotations"]:
            label = annotation.get("label")
            if label not in classes or annotation.get("visibility") != "visible":
                continue
            half = int(annotation["gameTime"].split(" - ", 1)[0])
            position = int(annotation["position"])
            if half not in (1, 2) or position < before:
                continue
            event_id = f"{game}|{half}|{position}|{label}"
            if event_id in seen:
                continue
            seen.add(event_id)
            result.append({
                "event_id": event_id,
                "match_path": game,
                "match_group": match_key(game),
                "half": half,
                "annotation_position_ms": position,
                "source_label": label,
                "class": classes[label],
                "start_ms": position - before,
                "end_ms": position + after,
                "source_visibility": "visible",
                "media_review": "pending",
            })
    return result


def select(pool: list[dict], roles: dict[str, str], config: dict) -> list[dict]:
    selected = []
    used_class_matches = set()
    occupied = defaultdict(list)
    # Rare penalty candidates first, followed by the other categories. This is
    # cohort construction using labels, never selection using model answers.
    for role in ROLES:
        for category in ("penalty", "free_kick", "corner"):
            eligible = sorted(
                (row for row in pool if row["class"] == category
                 and roles[row["match_group"]] == role),
                key=lambda row: rank(config["seed"], row["event_id"]),
            )
            primary = config["primary_clips_per_class"][role]
            target = primary + config["maximum_reserves_per_class_per_role"]
            picked = 0
            for row in eligible:
                group = (row["match_group"], category)
                half_group = (row["match_group"], row["half"])
                if group in used_class_matches:
                    continue
                if any(row["start_ms"] < end and row["end_ms"] > start
                       for start, end in occupied[half_group]):
                    continue
                selected.append({
                    **row,
                    "role": role,
                    "selection": "primary" if picked < primary else "reserve",
                    "class_rank": picked + 1,
                })
                used_class_matches.add(group)
                occupied[half_group].append((row["start_ms"], row["end_ms"]))
                picked += 1
                if picked == target:
                    break
            if picked < primary:
                raise ValueError(
                    f"Insufficient distinct-match {category} candidates in {role}: "
                    f"{picked} available, {primary} required. No freeze written."
                )
    for i, row in enumerate(sorted(selected, key=lambda r: rank(config["seed"], r["event_id"])), 1):
        row["clip_id"] = f"E-{i:04d}"
    return sorted(selected, key=lambda r: r["clip_id"])


def assert_disjoint(rows: list[dict]) -> None:
    roles_by_match = defaultdict(set)
    intervals = defaultdict(list)
    ids = set()
    for row in rows:
        if row["clip_id"] in ids:
            raise ValueError("Duplicate neutral clip ID")
        ids.add(row["clip_id"])
        roles_by_match[row["match_group"]].add(row["role"])
        key = (row["match_group"], row["half"])
        for start, end in intervals[key]:
            if row["start_ms"] < end and row["end_ms"] > start:
                raise ValueError("Overlapping clip windows")
        intervals[key].append((row["start_ms"], row["end_ms"]))
    if any(len(roles) != 1 for roles in roles_by_match.values()):
        raise ValueError("A match crosses roles")


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def freeze(config_path: Path, allow_fetch: bool) -> None:
    config = json.loads(config_path.read_bytes())
    freeze_path = ROOT / config["freeze_record"]
    if freeze_path.exists():
        raise ValueError("Selection already frozen; use verify. Refusing overwrite.")
    games, documents, sources = read_sources(config, allow_fetch)
    pool = candidates(documents, config)
    roles = group_roles(games, config, pool)
    print("Eligible visible train events:", dict(Counter(r["class"] for r in pool)), flush=True)
    rows = select(pool, roles, config)
    assert_disjoint(rows)
    base = ROOT / config["workspace"] / "private_selection"
    files = {
        base / "match_roles.json": encoded({g: roles[match_key(g)] for g in games}),
        base / "all_candidates.json": encoded(pool),
        base / "clip_selection.json": encoded(rows),
    }
    fields = ["clip_id", "role", "selection", "class", "source_label", "match_path",
              "half", "annotation_position_ms", "start_ms", "end_ms", "media_review"]
    for role in ROLES:
        files[base / f"{role}.csv"] = csv_bytes([r for r in rows if r["role"] == role], fields)
    if any(path.exists() for path in files):
        raise ValueError("Selection artifact already exists; refusing overwrite")
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    counts = {
        role: {category: sum(r["role"] == role and r["class"] == category
                             and r["selection"] == "primary" for r in rows)
               for category in config["classes"]}
        for role in ROLES
    }
    lock = {
        "experiment_id": config["experiment_id"],
        "status": "annotation_selection_frozen_media_and_reference_review_pending",
        "source_split": "official train only",
        "role_note": "held_out_test is an internal holdout, not the official SoccerNet test split",
        "config_path": config_path.relative_to(ROOT).as_posix(),
        "config_sha256": digest(config_path.read_bytes()),
        "builder_path": Path(__file__).relative_to(ROOT).as_posix(),
        "builder_sha256": digest(Path(__file__).read_bytes()),
        "primary_counts": counts,
        "reserve_count": sum(r["selection"] == "reserve" for r in rows),
        "selected_match_count": len({r["match_group"] for r in rows}),
        "match_overlap_across_roles": 0,
        "source_cache_hashes": sources,
        "selection_hashes": {p.relative_to(ROOT).as_posix(): digest(raw)
                             for p, raw in files.items()},
        "media_downloaded": False,
        "pixel_duplicate_audit": "pending",
        "prior_dataset_b_match_overlap_audit": "pending",
        "model_runs_allowed": False,
    }
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_bytes(encoded(lock))
    print(f"Frozen primary counts: {counts}")
    print(f"Frozen {lock['reserve_count']} reserves; {lock['selected_match_count']} matches")
    print(f"Freeze: {freeze_path}")
    print("Footage, pixel duplicate audit and human review are pending; no model calls allowed.")


def verify(config_path: Path) -> None:
    config = json.loads(config_path.read_bytes())
    lock = json.loads((ROOT / config["freeze_record"]).read_bytes())
    if digest(config_path.read_bytes()) != lock["config_sha256"]:
        raise ValueError("Frozen experiment declaration changed")
    if digest(Path(__file__).read_bytes()) != lock["builder_sha256"]:
        raise ValueError("Frozen selection builder changed")
    for path, expected in {**lock["source_cache_hashes"], **lock["selection_hashes"]}.items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise ValueError(f"Frozen source or selection changed: {path}")
    selection = ROOT / config["workspace"] / "private_selection/clip_selection.json"
    rows = json.loads(selection.read_bytes())
    assert_disjoint(rows)
    actual_counts = {
        role: {category: sum(r["role"] == role and r["class"] == category
                             and r["selection"] == "primary" for r in rows)
               for category in config["classes"]}
        for role in ROLES
    }
    if actual_counts != lock["primary_counts"]:
        raise ValueError("Frozen cohort counts disagree")
    print(f"Verified {len(rows)} candidate selections, source hashes and disjoint matches.")
    print(f"Execution status: {lock['status']}; model_runs_allowed={lock['model_runs_allowed']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "verify"))
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--fetch-public-labels", action="store_true")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(args.config.resolve(), args.fetch_public_labels)
    else:
        verify(args.config.resolve())


if __name__ == "__main__":
    main()
