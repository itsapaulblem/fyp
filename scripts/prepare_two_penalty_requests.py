"""Prepare offline requests only. Never contacts Ollama or runs a model."""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "input_prompts/in_context_events/two_penalty_examples_v1"
OUT = ROOT / "artifacts/in_context_events/two_penalty_examples_v1/prepared_requests"
MODEL = "qwen3.5:27b"
OPTIONS = {"temperature": 0, "seed": 20260903, "num_ctx": 32768, "num_gpu": 0}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def images(role, clip):
    folder = ROOT / f"artifacts/in_context_events/v1/frames/{role}/penalty/{clip}"
    paths = sorted(folder.glob("*.jpg"))
    expected = [f"{i:02d}.jpg" for i in range(1, 31)]
    if [p.name for p in paths] != expected:
        raise ValueError(f"Expected exactly 01.jpg–30.jpg: {folder}")
    records, encoded = [], []
    for path in paths:
        data = path.read_bytes()
        records.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest(data)})
        encoded.append(base64.b64encode(data).decode("ascii"))
    return records, encoded


def main():
    if OUT.exists():
        raise FileExistsError(f"Preserving existing prepared inputs: {OUT}")
    instruction = (PROMPTS / "recognition_instruction.v1.txt").read_text(encoding="utf-8").strip()
    descriptions = (PROMPTS / "example_descriptions.approved_v1.txt").read_text(encoding="utf-8")
    first = descriptions.split("DEMONSTRATION 1: E-0023\n", 1)[1].split("DEMONSTRATION 2: E-0117\n", 1)[0].strip()
    second = descriptions.split("DEMONSTRATION 2: E-0117\n", 1)[1].split("QUERY SEPARATION\n", 1)[0].strip()
    query_text = "BEGIN QUERY\nThe attached 30 images belong to one query clip and are ordered chronologically.\n\n" + instruction + "\nEND QUERY"
    q_records, q_images = images("development", "E-0127")
    records = {"query": q_records}
    demo_messages = []
    for index, (clip, description) in enumerate((("E-0023", first), ("E-0117", second)), 1):
        rows, encoded = images("example", clip)
        records[f"demonstration_{index}"] = rows
        demo_messages.append({"role": "user", "content": f"BEGIN DEMONSTRATION {index}\nThese 30 ordered images illustrate the following human-reviewed description:\n{description}\nEND DEMONSTRATION {index}", "images": encoded})
    # This check detects exact cross-clip copies, not perceptual duplicates or same-match footage.
    groups = list(records.values())
    for i, left in enumerate(groups):
        for right in groups[i + 1:]:
            if {r["sha256"] for r in left} & {r["sha256"] for r in right}:
                raise ValueError("Exact duplicate images across chosen clips; preparation stopped")
    query = {"role": "user", "content": query_text, "images": q_images}
    requests = {}
    for arm, messages in (("baseline", [query]), ("with_examples", demo_messages + [query])):
        requests[arm] = {"model": MODEL, "messages": messages, "options": OPTIONS, "think": False, "stream": False, "keep_alive": "10m"}
    assert requests["baseline"]["messages"][-1] == requests["with_examples"]["messages"][-1]
    OUT.mkdir(parents=True)
    file_hashes = {}
    for arm, request in requests.items():
        payload = (json.dumps(request, indent=2) + "\n").encode("utf-8")
        (OUT / f"{arm}_request.json").write_bytes(payload)
        file_hashes[f"{arm}_request.json"] = digest(payload)
        text = "\n\n".join(message["content"] for message in request["messages"]) + "\n"
        (OUT / f"{arm}_prompt.txt").write_bytes(text.encode("utf-8"))
        file_hashes[f"{arm}_prompt.txt"] = digest(text.encode("utf-8"))
    frozen = {"variant": "two_penalty_examples_v1", "query": "E-0127", "examples": ["E-0023", "E-0117"], "model": MODEL, "options": OPTIONS,
              "image_counts": {"baseline": 30, "with_examples": 90}, "images": records,
              "prepared_file_sha256": file_hashes,
              "source_file_sha256": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in [PROMPTS / "recognition_instruction.v1.txt", PROMPTS / "example_descriptions.approved_v1.txt", Path(__file__)]},
              "overlap": {"researcher_confirmation": "No overlap, confirmed in chat on 2026-10-11", "exact_cross_clip_duplicates": 0, "automated_match_and_near_duplicate_checks": "not performed by this preparer"},
              "limitations": ["Category-matched, label-informed development pilot", "Both demonstrations score; potential outcome bias", "Context retention not verified", "No previous model answers or query reference supplied"],
              "execution_allowed": False, "coaching_allowed": False}
    payload = (json.dumps(frozen, indent=2) + "\n").encode("utf-8")
    (OUT / "prepared_inputs.json").write_bytes(payload)
    (OUT / "prepared_inputs.sha256").write_bytes((digest(payload) + "  prepared_inputs.json\n").encode("ascii"))
    print(f"Prepared baseline (30 images) and two-example (90 images) requests: {OUT}")
    print("Exact query message and settings match. No model calls. Remote execution still requires a declared runner.")


if __name__ == "__main__":
    main()
