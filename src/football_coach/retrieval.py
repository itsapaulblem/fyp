from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class RetrievalHit:
    case_id: str
    similarity: float
    rank: int


class EmbeddingIndex:
    def __init__(
        self,
        case_ids: list[str],
        vectors: np.ndarray,
        metadata: dict[str, object] | None = None,
    ):
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2:
            raise ValueError("vectors must be a two-dimensional matrix")
        if matrix.shape[0] != len(case_ids):
            raise ValueError("case_ids and vectors must have the same row count")
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("case_ids must be unique")
        norms = np.linalg.norm(matrix, axis=1)
        if np.any(norms == 0):
            raise ValueError("zero-length embeddings are not searchable")
        self.case_ids = tuple(case_ids)
        self.vectors = matrix / norms[:, None]
        self.metadata = dict(metadata or {})

    def search(
        self,
        query_vector: np.ndarray,
        k: int,
        allowed_ids: set[str] | None = None,
    ) -> list[RetrievalHit]:
        query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        if query.shape[0] != self.vectors.shape[1]:
            raise ValueError("query and index embedding dimensions differ")
        norm = np.linalg.norm(query)
        if norm == 0:
            raise ValueError("query embedding has zero length")
        if k < 1:
            raise ValueError("k must be at least one")
        similarities = self.vectors @ (query / norm)
        candidates = [
            (self.case_ids[index], float(similarities[index]))
            for index in range(len(self.case_ids))
            if allowed_ids is None or self.case_ids[index] in allowed_ids
        ]
        candidates.sort(key=lambda item: (-item[1], item[0]))
        return [
            RetrievalHit(case_id=case_id, similarity=score, rank=rank)
            for rank, (case_id, score) in enumerate(candidates[:k], start=1)
        ]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            case_ids=np.array(self.case_ids),
            vectors=self.vectors,
            metadata_json=np.array(json.dumps(self.metadata, sort_keys=True)),
        )

    @classmethod
    def load(cls, path: Path) -> EmbeddingIndex:
        with np.load(path, allow_pickle=False) as payload:
            ids = [str(item) for item in payload["case_ids"].tolist()]
            vectors = payload["vectors"]
            metadata = (
                json.loads(str(payload["metadata_json"].item()))
                if "metadata_json" in payload.files
                else {}
            )
        return cls(ids, vectors, metadata)
