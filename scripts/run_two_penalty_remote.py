"""Separate researcher-authorized exploratory pilot; recognition only."""
import argparse
import base64
import hashlib
import json
import tarfile
import time
import traceback
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "artifacts/in_context_events/two_penalty_examples_v1/prepared_requests"
OUTPUT = ROOT / "output/in_context_events/two_penalty_examples_v1/e0127_exploratory_v1"
DIGEST = "193ec05b1e8048df17f7b8d15528671ae40e1a25cf4e0f5416c02b9cac5b990c"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def api(path, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request("http://127.0.0.1:11434" + path, data=data,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def validate():
    raw = (INPUT / "prepared_inputs.json").read_bytes()
    expected = (INPUT / "prepared_inputs.sha256").read_text().split()[0]
    if sha(raw) != expected:
        raise ValueError("Prepared-input manifest checksum mismatch")
    frozen = json.loads(raw)
    for name, expected in frozen["prepared_file_sha256"].items():
        if sha((INPUT / name).read_bytes()) != expected:
            raise ValueError(f"Frozen request/prompt changed: {name}")
    requests = {arm: json.loads((INPUT / f"{arm}_request.json").read_bytes())
                for arm in ("baseline", "with_examples")}
    for arm, request in requests.items():
        groups = ["query"] if arm == "baseline" else ["demonstration_1", "demonstration_2", "query"]
        if request["model"] != "qwen3.5:27b" or request["options"] != frozen["options"]:
            raise ValueError("Model/settings mismatch")
        if request.get("think") is not False or request.get("stream") is not False:
            raise ValueError("Thinking/stream settings mismatch")
        if len(request["messages"]) != len(groups):
            raise ValueError("Unexpected request history")
        for message, group in zip(request["messages"], groups):
            records = frozen["images"][group]
            if message["role"] != "user" or len(message["images"]) != 30 or len(records) != 30:
                raise ValueError("Expected 30 images per clip, user messages only")
            for encoded, record in zip(message["images"], records):
                if sha(base64.b64decode(encoded, validate=True)) != record["sha256"]:
                    raise ValueError("Encoded image hash mismatch")
    if requests["baseline"]["messages"][-1] != requests["with_examples"]["messages"][-1]:
        raise ValueError("Query differs between conditions")
    print("Validated baseline: 30 images; with_examples: 90 images; identical query and settings.", flush=True)
    return frozen, requests


def bundle():
    validate()
    target = ROOT / "artifacts/transfer/two_penalty_e0127_v1.tar.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"Preserving bundle: {target}")
    with tarfile.open(target, "w:gz") as archive:
        for path in sorted(INPUT.iterdir()):
            if path.is_file():
                archive.add(path, arcname=path.relative_to(ROOT).as_posix())
        archive.add(Path(__file__), arcname="scripts/run_two_penalty_remote.py")
    checksum = sha(target.read_bytes())
    target.with_name(target.name + ".sha256").write_bytes((checksum + "  " + target.name + "\n").encode("ascii"))
    print(f"Bundle: {target}\nSHA-256: {checksum}\nNo model calls.")


def run():
    frozen, requests = validate()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    save(OUTPUT / "prepared_inputs.json", frozen)
    save(OUTPUT / "execution_declaration.json", {
        "researcher_authorization": "2026-10-11: run remotely with tmux",
        "scope": "E-0127 baseline and E-0023/E-0117 demonstration recognition requests only",
        "variant": "category-matched label-informed exploratory development pilot",
        "recognition_approved": False, "coaching_allowed": False,
        "original_prepared_execution_allowed": frozen["execution_allowed"],
        "overlap": frozen["overlap"], "limitations": frozen["limitations"],
        "global_dataset_media_and_reference_gates": "not certified by this runner",
        "context_retention": "not verified; no automatic sampling reduction"})
    failures = []
    try:
        runtime = {"version": api("/api/version"), "tags": api("/api/tags"), "ps": api("/api/ps")}
        save(OUTPUT / "runtime_before.json", runtime)
        matches = [m for m in runtime["tags"].get("models", []) if m.get("name") == "qwen3.5:27b"]
        if len(matches) != 1 or matches[0].get("digest") != DIGEST:
            raise ValueError("Exact frozen Qwen model digest unavailable; no model calls")
        for arm, request in requests.items():
            folder = OUTPUT / arm
            folder.mkdir()
            (folder / "request.json").write_bytes((INPUT / f"{arm}_request.json").read_bytes())
            (folder / "prompt.txt").write_bytes((INPUT / f"{arm}_prompt.txt").read_bytes())
            save(folder / "settings.json", {"model": request["model"], "digest": DIGEST,
                 "options": request["options"], "think": False, "stream": False})
            count = sum(len(message["images"]) for message in request["messages"])
            status = {"state": "started", "image_count": count, "started_utc": datetime.now(timezone.utc).isoformat()}
            save(folder / "status.json", status)
            print(f"Starting {arm}: {count} images; recognition only.", flush=True)
            started = time.monotonic()
            try:
                result = api("/api/chat", request, timeout=14400)
                save(folder / "raw_api_response.json", result)
                if result.get("error") or not result.get("done") or not isinstance(result.get("message", {}).get("content"), str):
                    raise ValueError("API result is an error or incomplete; raw response preserved")
                (folder / "response.txt").write_text(result["message"]["content"], encoding="utf-8")
                residency = api("/api/ps")
                save(folder / "residency_after.json", residency)
                loaded = [m for m in residency.get("models", []) if m.get("digest") == DIGEST]
                if len(loaded) != 1 or loaded[0].get("size_vram") != 0 or loaded[0].get("context_length") != 32768:
                    raise ValueError("Response preserved but CPU/context residency verification failed")
                status.update(state="completed", prompt_eval_count=result.get("prompt_eval_count"), eval_count=result.get("eval_count"))
                print(f"Preserved {arm}: {folder}", flush=True)
            except Exception as error:
                failures.append(arm)
                record = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
                if hasattr(error, "read"):
                    record["raw_http_body"] = error.read().decode("utf-8", errors="replace")
                save(folder / "error.json", record)
                status["state"] = "failed"
                print(f"Failed {arm}: {error}; preserved; no retry.", flush=True)
            finally:
                status["elapsed_seconds"] = time.monotonic() - started
                save(folder / "status.json", status)
    except Exception as error:
        failures.append("preflight_or_batch")
        save(OUTPUT / "batch_error.json", {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
        print(f"Batch error: {error}", flush=True)
    finally:
        save(OUTPUT / "batch_status.json", {"ended": True, "failures": failures, "coaching": False})
        target = ROOT / "two_penalty_e0127_v1_results.tar.gz"
        if target.exists():
            raise FileExistsError(f"Preserving existing results archive: {target}")
        with tarfile.open(target, "w:gz") as archive:
            archive.add(OUTPUT, arcname=OUTPUT.relative_to(ROOT).as_posix())
        print(f"Batch ended; failures={failures}; no coaching.\nResults: {target}\nSHA-256: {sha(target.read_bytes())}", flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bundle", action="store_true")
    group.add_argument("--validate-only", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.bundle:
        bundle()
    elif args.validate_only:
        validate()
        print("No model calls.")
    else:
        run()
