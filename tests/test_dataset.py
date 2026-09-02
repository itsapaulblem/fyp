from football_coach.dataset import ClipRecord, select_records


def record(clip_id: str, split: str, action: str) -> ClipRecord:
    return ClipRecord(
        clip_id,
        split,
        action,
        "1",
        "1 - 00:00",
        "1 - 00:30",
        25,
        750,
        30.0,
        "1.3",
        "x.zip",
        "label",
        "%06d.jpg",
    )


def test_selection_is_deterministic_and_covers_classes() -> None:
    records = []
    for split in ("train", "valid", "test"):
        records.extend(
            record(f"{split}-{i:03d}", split, "shot" if i < 8 else "corner")
            for i in range(10)
        )
    targets = {"train": 6, "valid": 6, "test": 6}
    first, allocations = select_records(records, targets, seed=42)
    second, _ = select_records(records, targets, seed=42)
    assert first == second
    assert len(first) == 18
    assert all(allocations[split]["corner"] >= 1 for split in targets)
