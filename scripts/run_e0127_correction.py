"""Offline packaging and remote-only explicit correction; no demonstrations/coaching."""
import argparse
import base64
import json
import tarfile
import time
import traceback
from pathlib import Path
from run_two_penalty_remote import api, sha, save, DIGEST

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "artifacts/in_context_events/e0127_explicit_correction_v1/frozen_inputs"
OUTPUT = ROOT / "output/in_context_events/e0127_explicit_correction_v1/recognition_revision"


def validate():
    raw = (INPUT / "freeze.json").read_bytes()
    if sha(raw) != (INPUT / "freeze.sha256").read_text().split()[0]:
        raise ValueError("Freeze checksum mismatch")
    freeze = json.loads(raw)
    for name, expected in freeze["files"].items():
        if sha((INPUT / name).read_bytes()) != expected:
            raise ValueError(f"Frozen file changed: {name}")
    for name, expected in freeze["runner_files"].items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Runner changed: {name}")
    request = json.loads((INPUT / "request.json").read_bytes())
    if [m["role"] for m in request["messages"]] != ["user", "assistant", "user"]:
        raise ValueError("Unexpected conversation roles")
    if [len(m["images"]) for m in request["messages"]] != [30, 0, 0]:
        raise ValueError("Expected only 30 query images, no demonstration images")
    for encoded, record in zip(request["messages"][0]["images"], freeze["query_images"]):
        if sha(base64.b64decode(encoded, validate=True)) != record["sha256"]:
            raise ValueError("Query image hash mismatch")
    if len(freeze["query_images"]) != 30 or request["options"] != freeze["options"] or request["model"] != "qwen3.5:27b":
        raise ValueError("Frozen model/settings mismatch")
    print("Validated E-0127: 30 query images, prior answer, explicit correction; no demonstrations/coaching.", flush=True)
    return freeze, request


def bundle():
    from run_two_penalty_remote import validate as validate_parent
    parent, requests = validate_parent()
    if INPUT.exists():
        raise FileExistsError(f"Preserving prepared correction: {INPUT}")
    target = ROOT / "artifacts/transfer/e0127_explicit_correction_v1.tar.gz"
    if target.exists():
        raise FileExistsError(f"Preserving bundle: {target}")
    source = ROOT / "output/in_context_events/two_penalty_examples_v1/e0127_exploratory_v1/with_examples"
    prior = (source / "response.txt").read_bytes()
    previous_request = json.loads((source / "request.json").read_bytes())
    if previous_request != requests["with_examples"]:
        raise ValueError("Imported failed answer's request differs from frozen parent request")
    correction_path = ROOT / "input_prompts/in_context_events/e0127_explicit_correction_v1/human_correction.txt"
    correction = correction_path.read_bytes()
    request = dict(requests["baseline"])
    request["messages"] = [requests["baseline"]["messages"][0],
        {"role": "assistant", "content": prior.decode("utf-8"), "images": []},
        {"role": "user", "content": correction.decode("utf-8"), "images": []}]
    INPUT.mkdir(parents=True)
    blobs = {"request.json": (json.dumps(request, indent=2) + "\n").encode("utf-8"),
             "previous_answer.txt": prior, "human_correction.txt": correction,
             "prompt.txt": ("\n\n".join(m["role"].upper() + "\n" + m["content"] for m in request["messages"]) + "\n").encode("utf-8")}
    for name, data in blobs.items():
        (INPUT / name).write_bytes(data)
    runner_paths = ["scripts/run_e0127_correction.py", "scripts/run_two_penalty_remote.py"]
    freeze = {"variant": "e0127_explicit_correction_v1", "query": "E-0127", "query_images": parent["images"]["query"],
        "model": request["model"], "model_digest": DIGEST, "options": request["options"],
        "files": {name: sha(data) for name, data in blobs.items()},
        "runner_files": {name: sha((ROOT / name).read_bytes()) for name in runner_paths},
        "parent_manifest_sha256": sha((ROOT / "artifacts/in_context_events/two_penalty_examples_v1/prepared_requests/prepared_inputs.json").read_bytes()),
        "prior_answer_source": (source / "response.txt").relative_to(ROOT).as_posix(),
        "declaration": "Researcher-authorized separate human-assisted development correction; condensed history omits both demonstrations; not independent recognition.",
        "coaching_allowed": False, "recognition_approved": False}
    save(INPUT / "freeze.json", freeze)
    (INPUT / "freeze.sha256").write_bytes((sha((INPUT / "freeze.json").read_bytes()) + "  freeze.json\n").encode("ascii"))
    validate()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(target, "w:gz") as archive:
        for path in sorted(INPUT.iterdir()):
            archive.add(path, arcname=path.relative_to(ROOT).as_posix())
        for name in runner_paths:
            archive.add(ROOT / name, arcname=name)
    checksum = sha(target.read_bytes())
    target.with_name(target.name + ".sha256").write_bytes((checksum + "  " + target.name + "\n").encode("ascii"))
    print(f"Bundle: {target}\nSHA-256: {checksum}\nNo model calls.")


def run():
    freeze, request = validate()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for path in INPUT.iterdir():
        (OUTPUT / path.name).write_bytes(path.read_bytes())
    started = time.monotonic()
    status = {"state": "preflight", "recognition_approved": False, "coaching": False}
    save(OUTPUT / "status.json", status)
    try:
        runtime = {"version": api("/api/version"), "tags": api("/api/tags"), "ps": api("/api/ps")}
        save(OUTPUT / "runtime_before.json", runtime)
        if not any(m.get("name") == "qwen3.5:27b" and m.get("digest") == DIGEST for m in runtime["tags"].get("models", [])):
            raise ValueError("Exact Qwen digest unavailable; no model call")
        status["state"] = "started"
        save(OUTPUT / "status.json", status)
        print("Starting explicit recognition correction: 30 query images; no coaching.", flush=True)
        result = api("/api/chat", request, timeout=14400)
        save(OUTPUT / "raw_api_response.json", result)
        if result.get("error") or not result.get("done") or not isinstance(result.get("message", {}).get("content"), str):
            raise ValueError("Incomplete/error API response preserved")
        (OUTPUT / "response.txt").write_text(result["message"]["content"], encoding="utf-8")
        residency = api("/api/ps")
        save(OUTPUT / "residency_after.json", residency)
        loaded = [m for m in residency.get("models", []) if m.get("digest") == DIGEST]
        if len(loaded) != 1 or loaded[0].get("size_vram") != 0 or loaded[0].get("context_length") != 32768:
            raise ValueError("Response preserved but CPU/context verification failed")
        status.update(state="completed", prompt_eval_count=result.get("prompt_eval_count"), eval_count=result.get("eval_count"))
        print(f"Preserved recognition correction: {OUTPUT}", flush=True)
    except Exception as error:
        record = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        if hasattr(error, "read"):
            record["raw_http_body"] = error.read().decode("utf-8", errors="replace")
        save(OUTPUT / "error.json", record)
        status.update(state="failed", error=str(error))
    finally:
        status["elapsed_seconds"] = time.monotonic() - started
        save(OUTPUT / "status.json", status)
        target = ROOT / "e0127_explicit_correction_v1_results.tar.gz"
        if target.exists():
            raise FileExistsError(f"Preserving existing result archive: {target}")
        with tarfile.open(target, "w:gz") as archive:
            archive.add(OUTPUT, arcname=OUTPUT.relative_to(ROOT).as_posix())
        print(f"Correction ended; state={status['state']}; no coaching.\nResults: {target}\nSHA-256: {sha(target.read_bytes())}", flush=True)
    if status["state"] != "completed":
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
    else:
        run()
