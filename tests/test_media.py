import numpy as np
import pytest

from football_coach.media import uniform_positions, write_jpeg_without_overwrite


def test_uniform_positions_cover_sequence_boundaries() -> None:
    assert uniform_positions(750, 4) == [0, 250, 499, 749]


def test_single_position_uses_middle() -> None:
    assert uniform_positions(9, 1) == [4]


def test_invalid_uniform_request_fails() -> None:
    with pytest.raises(ValueError):
        uniform_positions(4, 5)


def test_sampled_frame_cannot_be_silently_overwritten(tmp_path) -> None:
    path = tmp_path / "frame.jpg"
    first = np.zeros((4, 4, 3), dtype=np.uint8)
    write_jpeg_without_overwrite(first, path)
    write_jpeg_without_overwrite(first, path)
    changed = np.full((4, 4, 3), 255, dtype=np.uint8)
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        write_jpeg_without_overwrite(changed, path)
