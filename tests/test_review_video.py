from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from football_dataset.review_video import _sha256


class ReviewVideoTests(unittest.TestCase):
    def test_sha256_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(b"SoccerNet review video")
            self.assertEqual(
                _sha256(path),
                "c8f6e85079f980730d9764af680c0804a68526df154c9fdf3d6f6697564e7372",
            )


if __name__ == "__main__":
    unittest.main()
