from pathlib import Path

import numpy as np

from football_coach.retrieval import EmbeddingIndex


def test_cosine_knn_returns_nearest_case() -> None:
    index = EmbeddingIndex(
        ["A-0001", "A-0002", "A-0003"],
        np.array([[1, 0], [0, 1], [-1, 0]], dtype=np.float32),
    )
    hits = index.search(np.array([0.9, 0.1]), k=2)
    assert [hit.case_id for hit in hits] == ["A-0001", "A-0002"]
    assert hits[0].rank == 1


def test_embedding_index_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "index.npz"
    EmbeddingIndex(["A-0001"], np.array([[3, 4]], dtype=np.float32)).save(path)
    loaded = EmbeddingIndex.load(path)
    assert loaded.search(np.array([3, 4]), 1)[0].similarity == 1.0

