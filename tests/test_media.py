import pytest

from football_coach.media import uniform_indices


def test_uniform_indices_include_first_and_last_frame() -> None:
    indices = uniform_indices(750, 8)
    assert indices[0] == 1
    assert indices[-1] == 750
    assert indices == sorted(set(indices))


def test_uniform_indices_reject_invalid_count() -> None:
    with pytest.raises(ValueError):
        uniform_indices(8, 9)

