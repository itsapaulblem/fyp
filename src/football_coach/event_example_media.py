"""Download frozen SoccerNet train candidates and extract neutral-ID sampled frames.

No inference or reference approval is performed. Protected media stays local.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import ssl
from collections import defaultdict
from pathlib import Path

import cv2
import httpx
from huggingface_hub import HfApi, get_token, hf_hub_url, set_client_factory

from .event_examples import CONFIG, ROOT, assert_disjoint, verify
from .media import resize_max_edge, uniform_positions, write_jpeg_without_overwrite

REPO = "SoccerNet/SoccerNet_raw_HQ"
REVISION = "93544d42a32237e0f580f021d137b1822631f55c"
BASE = ROOT / "artifacts/in_context_events/v1"


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def source_path(row: dict) -> str:
    return f"{row['match_path']}/{row['half']}_720p.mkv"


def frame_directory(row: dict) -> Path:
    return BASE / "frames" / row["role"] / row["class"] / row["clip_id"]


def complete(row: dict) -> bool:
    record = BASE / "media_records/clips" / f"{row['clip_id']}.json"
    if not record.exists():
        return False
    manifest = json.loads(record.read_bytes())
    if manifest["candidate"] != row or manifest["source_revision"] != REVISION:
        raise ValueError(f"Existing media provenance differs: {row['clip_id']}")
    for frame in manifest["frames"]:
        path = ROOT / frame["path"]
        if not path.exists() or sha(path) != frame["sha256"]:
            raise ValueError(f"Existing sampled image missing or changed: {path}")
    return len(manifest["frames"]) == 30


def amended_rows(all_rows: list[dict], amendment: dict) -> list[dict]:
    """Use explicitly approved reserves without rewriting frozen candidate records."""
    rows = [row for row in all_rows if row["selection"] == "primary"]
    lookup = {row["clip_id"]: row for row in all_rows}
    used = set()
    for entry in amendment["replacements"]:
        bad = lookup[entry["rejected_clip_id"]]
        reserve = lookup[entry["replacement_clip_id"]]
        if bad["selection"] != "primary" or reserve["selection"] != "reserve":
            raise ValueError("Amendment must replace a primary with a frozen reserve")
        if (bad["role"], bad["class"]) != (reserve["role"], reserve["class"]):
            raise ValueError("Reserve must remain in the same role and category")
        if bad["clip_id"] in used or reserve["clip_id"] in used:
            raise ValueError("Duplicate replacement in amendment")
        eligible = sorted((row for row in all_rows if row["selection"] == "reserve"
                           and row["role"] == bad["role"] and row["class"] == bad["class"]
                           and row["clip_id"] not in used), key=lambda row: row["class_rank"])
        if reserve != eligible[0]:
            raise ValueError("Amendment must use the first eligible frozen reserve")
        if (bad["start_ms"], bad["end_ms"]) != (
                entry["reported_start_ms"], entry["reported_end_ms"]):
            raise ValueError("Reported window differs from frozen candidate")
        used.update((bad["clip_id"], reserve["clip_id"]))
        rows = [row for row in rows if row["clip_id"] != bad["clip_id"]] + [reserve]
    assert_disjoint(rows)
    return rows


def verify_rejections(all_rows: list[dict], amendment: dict, amendment_sha: str) -> None:
    lookup = {row["clip_id"]: row for row in all_rows}
    for entry in amendment["replacements"]:
        bad = lookup[entry["rejected_clip_id"]]
        if complete(bad):
            raise ValueError("Refusing duration rejection for an already completed clip")
        record_path = BASE / "media_records/rejections" / f"{bad['clip_id']}.json"
        if record_path.exists():
            record = json.loads(record_path.read_bytes())
            if record["amendment_sha256"] != amendment_sha or record["candidate"] != bad:
                raise ValueError("Existing rejection does not match approved amendment")
            continue
        filename = source_path(bad)
        key = hashlib.sha256(filename.encode()).hexdigest()
        video = BASE / "temporary_footage" / f"{key}.mkv"
        source = json.loads((BASE / "media_records/sources" / f"{key}.json").read_bytes())
        if source["revision"] != REVISION or sha(video) != source["sha256"]:
            raise ValueError("Rejected source hash/revision does not match downloaded provenance")
        capture = cv2.VideoCapture(str(video))
        try:
            fps = capture.get(cv2.CAP_PROP_FPS)
            total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if not capture.isOpened() or not math.isfinite(fps) or fps <= 0 or total <= 0:
                raise ValueError("Cannot validate rejected source duration")
            duration = total / fps
            if abs(duration - entry["reported_source_duration_seconds"]) > 1 / fps:
                raise ValueError("Source duration differs from reported evidence")
            if round(bad["end_ms"] * fps / 1000) - 1 < total:
                raise ValueError("Frozen window fits; duration rejection is not supported")
        finally:
            capture.release()
        save(record_path, {
            "candidate": bad, "replacement_clip_id": entry["replacement_clip_id"],
            "amendment_sha256": amendment_sha, "reason": entry["reason"],
            "source_sha256": source["sha256"], "source_revision": REVISION,
            "source_frame_count": total, "fps": fps, "source_duration_seconds": duration,
            "original_window_preserved": True, "no_model_results_used": True,
        })
        print(f"Recorded duration rejection: {bad['clip_id']}; "
              f"frozen reserve {entry['replacement_clip_id']} activated.", flush=True)


def build_plan(rows: list[dict]) -> dict:
    wanted = {source_path(row) for row in rows}
    inventory = {
        item.path: {"bytes": item.size, "lfs": item.lfs}
        for item in HfApi().list_repo_tree(REPO, repo_type="dataset", revision=REVISION,
                                         recursive=True)
        if item.path in wanted
    }
    if wanted - inventory.keys():
        raise ValueError(f"Required source halves absent: {sorted(wanted - inventory.keys())}")
    return {
        "repository": REPO, "revision": REVISION,
        "selection_sha256": sha(BASE / "private_selection/clip_selection.json"),
        "clip_count": len(rows), "half_count": len(inventory),
        "total_download_bytes": sum(item["bytes"] for item in inventory.values()),
        "largest_half_bytes": max(item["bytes"] for item in inventory.values()),
        "sources": inventory, "model_runs_allowed": False,
    }


def download(filename: str, target: Path, expected: dict) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".mkv.partial")
    if not target.exists():
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"Authorization": f"Bearer {get_token()}"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        # httpx never forwards Authorization across an off-host CDN redirect.
        with httpx.Client(verify=ssl.create_default_context(), follow_redirects=True,
                          timeout=httpx.Timeout(120, connect=30)) as client:
            with client.stream("GET", hf_hub_url(REPO, filename, repo_type="dataset",
                                               revision=REVISION), headers=headers) as response:
                response.raise_for_status()
                if response.status_code == 206:
                    if not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                        raise ValueError("Incorrect download resume offset")
                    mode = "ab"
                else:
                    mode = "wb"
                with partial.open(mode) as stream:
                    for block in response.iter_bytes(1024 * 1024):
                        stream.write(block)
        if partial.stat().st_size != expected["bytes"]:
            raise ValueError("Source download size mismatch; partial retained for diagnosis")
        partial.replace(target)
    if target.stat().st_size != expected["bytes"]:
        raise ValueError("Existing source size mismatch")
    actual = sha(target)
    lfs = expected.get("lfs") or {}
    lfs_sha = lfs.get("sha256") if isinstance(lfs, dict) else getattr(lfs, "sha256", None)
    if lfs_sha and actual != lfs_sha:
        raise ValueError("Source SHA-256 does not match provider LFS hash")
    return actual


def extract(row: dict, video: Path, source_sha: str) -> None:
    capture = cv2.VideoCapture(str(video))
    try:
        if not capture.isOpened():
            raise ValueError("Cannot decode source video")
        fps = capture.get(cv2.CAP_PROP_FPS)
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if not math.isfinite(fps) or fps <= 0 or total <= 0:
            raise ValueError("Invalid source frame metadata")
        first = round(row["start_ms"] * fps / 1000)
        last = round(row["end_ms"] * fps / 1000) - 1
        if first < 0 or last >= total or last < first:
            raise ValueError("Frozen window exceeds source duration; do not silently truncate")
        indices = [first + value for value in uniform_positions(last - first + 1, 30)]
        destination = frame_directory(row)
        destination.mkdir(parents=True, exist_ok=True)
        frames = []
        for order, index in enumerate(indices, 1):
            if not capture.set(cv2.CAP_PROP_POS_FRAMES, index):
                raise ValueError(f"Seek failed at decoded index {index}")
            ok, frame = capture.read()
            position = round(capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            if not ok or frame is None or position != index:
                raise ValueError(f"Decode/seek mismatch at index {index}, got {position}")
            height, width = frame.shape[:2]
            frame = resize_max_edge(frame, 672)
            output = destination / f"{order:02d}.jpg"
            write_jpeg_without_overwrite(frame, output)
            frames.append({"path": output.relative_to(ROOT).as_posix(), "sha256": sha(output),
                           "sample_position_1_based": order, "decoded_frame_index_0_based": index,
                           "source_time_ms": index * 1000 / fps,
                           "source_dimensions": [width, height],
                           "image_dimensions": [frame.shape[1], frame.shape[0]]})
        save(BASE / "media_records/clips" / f"{row['clip_id']}.json", {
            "candidate": row, "source_repository": REPO, "source_revision": REVISION,
            "source_filename": source_path(row), "source_sha256": source_sha,
            "fps": fps, "source_frame_count": total, "frames": frames,
            "jpeg_quality": 92, "maximum_edge": 672,
            "human_visibility_review": "pending", "timestamp_alignment_review": "pending",
            "prior_GSR_overlap_audit": "pending", "near_duplicate_audit": "pending",
            "model_runs_allowed": False,
        })
    finally:
        capture.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "run", "status"])
    parser.add_argument("--discard-temporary-videos", action="store_true")
    parser.add_argument("--max-halves", type=int)
    parser.add_argument("--amendment", type=Path)
    args = parser.parse_args()
    verify(CONFIG)
    all_rows = json.loads((BASE / "private_selection/clip_selection.json").read_bytes())
    rows = [row for row in all_rows if row["selection"] == "primary"]
    amendment = None
    if args.amendment:
        amendment = json.loads(args.amendment.read_bytes())
        if (amendment["original_selection_sha256"] != sha(
                BASE / "private_selection/clip_selection.json") or
                amendment["original_freeze_sha256"] != sha(
                    ROOT / "config/freezes/in_context_event_selection_v1.json") or
                amendment["source_revision"] != REVISION):
            raise ValueError("Amendment does not match original frozen selection/source")
        rows = amended_rows(all_rows, amendment)
        print("Using explicit media amendment; original selection remains unchanged.", flush=True)
    if args.action == "status":
        finished = sum(complete(row) for row in rows)
        print(f"Progress: {finished}/{len(rows)} active clips extracted; reviews pending.")
        for role in ("example", "development", "held_out_test"):
            subset = [row for row in rows if row["role"] == role]
            print(f"  {role}: {sum(complete(row) for row in subset)}/{len(subset)}")
        return
    if not get_token():
        raise ValueError("Log in to Hugging Face first; never paste tokens into logs")
    set_client_factory(lambda: httpx.Client(verify=ssl.create_default_context(),
                                            follow_redirects=True))
    # Original plan is never overwritten by an amended plan.
    plan_path = BASE / "media_records" / (
        "download_plan_amendment_v1.json" if amendment else "download_plan.json")
    if plan_path.exists():
        plan = json.loads(plan_path.read_bytes())
        if plan["revision"] != REVISION or plan["selection_sha256"] != sha(
                BASE / "private_selection/clip_selection.json"):
            raise ValueError("Download plan does not match frozen candidates")
        if amendment and plan.get("amendment_sha256") != sha(args.amendment):
            raise ValueError("Existing amended plan belongs to another amendment")
    else:
        plan = build_plan(rows)
        if amendment:
            plan["amendment_sha256"] = sha(args.amendment)
        save(plan_path, plan)
    print(f"Plan: {plan['clip_count']} primary clips, {plan['half_count']} source halves; "
          f"{plan['total_download_bytes'] / 2**30:.1f} GiB transfer; "
          f"largest half {plan['largest_half_bytes'] / 2**30:.2f} GiB.", flush=True)
    if args.action == "plan":
        return
    if amendment:
        verify_rejections(all_rows, amendment, sha(args.amendment))
    for row in rows:
        frame_directory(row).mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[source_path(row)].append(row)
    processed = 0
    # Example/development first; held-out frames are extracted without examining content.
    groups = sorted(grouped.items(), key=lambda item: (
        {"example": 0, "development": 1, "held_out_test": 2}[item[1][0]["role"]], item[0]))
    for filename, candidates in groups:
        if all(complete(row) for row in candidates):
            continue
        if args.max_halves is not None and processed >= args.max_halves:
            break
        expected = plan["sources"][filename]
        if shutil.disk_usage(BASE).free < expected["bytes"] + 3 * 2**30:
            raise OSError("Insufficient disk space; need source half plus 3 GiB headroom")
        key = hashlib.sha256(filename.encode()).hexdigest()
        video = BASE / "temporary_footage" / f"{key}.mkv"
        print(f"Downloading half {processed + 1}: {len(candidates)} clips "
              f"({expected['bytes'] / 2**30:.2f} GiB)", flush=True)
        source_sha = download(filename, video, expected)
        save(BASE / "media_records/sources" / f"{key}.json", {
            "filename": filename, "revision": REVISION, "sha256": source_sha,
            "bytes": video.stat().st_size, "retention": "temporary" if
            args.discard_temporary_videos else "retained",
        })
        for row in candidates:
            if not complete(row):
                extract(row, video, source_sha)
            print(f"Extracted {row['clip_id']}: 30 frames; review pending.", flush=True)
        if args.discard_temporary_videos:
            # Only this explicitly named, hash-addressed downloaded half is removed.
            if video.resolve().parent != (BASE / "temporary_footage").resolve():
                raise ValueError("Temporary source path escaped its intended directory")
            video.unlink()
        processed += 1
    finished = sum(complete(row) for row in rows)
    print(f"Progress: {finished}/{len(rows)} active clips extracted; no model calls.", flush=True)


if __name__ == "__main__":
    main()
