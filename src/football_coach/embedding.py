from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class ClipFrameEncoder:
    """Frozen CLIP image encoder with transparent temporal mean pooling."""

    def __init__(self, model_id: str, revision: str, device: str | None = None):
        try:
            torch = importlib.import_module("torch")
            transformers = importlib.import_module("transformers")
        except ImportError as error:
            raise RuntimeError(
                "CLIP retrieval dependencies are missing; run `uv sync --extra retrieval`"
            ) from error
        self._torch = torch
        self.model_id = model_id
        self.revision = revision
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = transformers.AutoProcessor.from_pretrained(model_id, revision=revision)
        self.model = transformers.CLIPModel.from_pretrained(model_id, revision=revision)
        self.model.eval().to(self.device)

    def encode_frames(
        self,
        paths: list[Path],
        batch_size: int = 16,
        progress: Callable[[str], None] | None = None,
    ) -> np.ndarray:
        if not paths:
            raise ValueError("At least one frame is required")
        batches: list[np.ndarray] = []
        with self._torch.inference_mode():
            for start in range(0, len(paths), batch_size):
                batch_paths = paths[start : start + batch_size]
                images = []
                for path in batch_paths:
                    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
                    if frame is None:
                        raise ValueError(f"Could not decode frame for embedding: {path}")
                    images.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                inputs = self.processor(images=images, return_tensors="pt")
                pixel_values = inputs["pixel_values"].to(self.device)
                features: Any = self.model.get_image_features(pixel_values=pixel_values)
                if hasattr(features, "image_embeds"):
                    features = features.image_embeds
                features = features / features.norm(dim=-1, keepdim=True)
                batches.append(features.detach().cpu().numpy().astype(np.float32))
                if progress:
                    progress(f"Embedded {min(start + batch_size, len(paths))}/{len(paths)} frames")
        per_frame = np.concatenate(batches, axis=0)
        pooled = per_frame.mean(axis=0)
        norm = np.linalg.norm(pooled)
        if norm == 0:
            raise ValueError("Temporal mean produced a zero-length embedding")
        return (pooled / norm).astype(np.float32)

    def provenance(self) -> dict[str, object]:
        return {
            "encoder_family": "CLIP",
            "model_id": self.model_id,
            "revision": self.revision,
            "device": self.device,
            "preprocessing": "AutoProcessor from pinned model revision",
            "frame_aggregation": (
                "mean of per-frame L2-normalized image embeddings, then L2 normalize"
            ),
            "uses_dataset_b_labels_or_text": False,
        }
