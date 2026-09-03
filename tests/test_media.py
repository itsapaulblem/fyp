import pytest

from football_coach.media import uniform_positions


def test_uniform_positions_cover_sequence_boundaries() -> None:
    assert uniform_positions(750, 4) == [0, 250, 499, 749]


def test_single_position_uses_middle() -> None:
    assert uniform_positions(9, 1) == [4]


def test_invalid_uniform_request_fails() -> None:
    with pytest.raises(ValueError):
        uniform_positions(4, 5)

