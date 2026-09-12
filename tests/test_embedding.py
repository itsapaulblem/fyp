from types import SimpleNamespace

from football_coach.embedding import _extract_clip_image_features


def test_extract_clip_image_features_keeps_legacy_tensor() -> None:
    tensor = object()
    assert _extract_clip_image_features(tensor) is tensor


def test_extract_clip_image_features_uses_image_embeds() -> None:
    tensor = object()
    output = SimpleNamespace(image_embeds=tensor)
    assert _extract_clip_image_features(output) is tensor


def test_extract_clip_image_features_uses_transformers_5_pooler_output() -> None:
    tensor = object()
    output = SimpleNamespace(pooler_output=tensor)
    assert _extract_clip_image_features(output) is tensor
