from __future__ import annotations

import unittest

from football_dataset.pilot import (
    EVENT_OFFSETS_SECONDS,
    RESPONSE_SCHEMA,
    event_centered_frames,
    event_frame_from_info,
    uniform_frames,
)


class SamplingTests(unittest.TestCase):
    def test_response_schema_matches_required_protocol_fields(self) -> None:
        self.assertEqual(
            set(RESPONSE_SCHEMA["required"]), set(RESPONSE_SCHEMA["properties"])
        )
        self.assertEqual(RESPONSE_SCHEMA["properties"]["limitations"]["maxItems"], 3)

    def test_uniform_sampling_has_16_unique_ordered_frames(self) -> None:
        frames = uniform_frames()
        self.assertEqual(len(frames), 16)
        self.assertEqual(frames, sorted(set(frames)))
        self.assertGreaterEqual(frames[0], 1)
        self.assertLessEqual(frames[-1], 750)

    def test_event_sampling_has_16_unique_ordered_frames(self) -> None:
        for event_frame in (1, 173, 375, 750):
            frames = event_centered_frames(event_frame)
            self.assertEqual(len(frames), len(EVENT_OFFSETS_SECONDS))
            self.assertEqual(frames, sorted(set(frames)))
            self.assertGreaterEqual(frames[0], 1)
            self.assertLessEqual(frames[-1], 750)

    def test_event_frame_uses_millisecond_metadata(self) -> None:
        info = {
            "action_position": "2577866",
            "clip_start": "2571000",
            "frame_rate": 25,
            "seq_length": 750,
        }
        self.assertEqual(event_frame_from_info(info), 173)


if __name__ == "__main__":
    unittest.main()
