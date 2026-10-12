import pytest

from football_coach.in_context_comparison import save_once


def test_freeze_preserves_exact_bytes(tmp_path):
    path = tmp_path / 'freeze.txt'
    save_once(path, b'approved\n')
    save_once(path, b'approved\n')
    with pytest.raises(ValueError, match='Existing frozen file differs'):
        save_once(path, b'changed\n')
    assert path.read_bytes() == b'approved\n'


def test_nested_freeze_directory(tmp_path):
    path = tmp_path / 'nested' / 'freeze.txt'
    save_once(path, b'fixed')
    assert path.read_bytes() == b'fixed'
