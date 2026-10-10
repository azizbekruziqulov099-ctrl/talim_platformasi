"""REV93: aralash tilli ovoz — bo'lak chetidagi jimlik MP3 kadr chegarasida kesiladi."""
import unittest

from modules.speech_audio import mp3_frames, speech_window, trim_segment


def frame():   # MPEG2 Layer III, 48 kbps, 24 kHz (edge-tts formati): 144 bayt, 24 ms
    return bytes([0xFF, 0xF3, 0x64, 0xC4]) + bytes(140)


class TrimTests(unittest.TestCase):
    def test_frames_are_parsed(self):
        data = frame() * 50
        frames = mp3_frames(data)
        self.assertEqual(len(frames), 50)
        self.assertAlmostEqual(frames[0][2], 0.024)

    def test_silence_around_speech_is_cut(self):
        data = frame() * 100   # 2.4 s
        out = trim_segment(data, 0.5, 1.5)
        kept = len(out) // 144
        self.assertTrue(44 <= kept <= 50, kept)   # ~1.0 s nutq + 0.04 + 0.14 s chet
        self.assertEqual(len(out) % 144, 0)

    def test_unknown_data_is_left_untouched(self):
        self.assertEqual(trim_segment(b"not mp3 at all", 0.1, 0.5), b"not mp3 at all")
        self.assertEqual(trim_segment(frame() * 10, None, None), frame() * 10)

    def test_window_from_boundary_events(self):
        events = [{"type": "WordBoundary", "offset": 1_000_000, "duration": 2_000_000},
                  {"type": "WordBoundary", "offset": 5_000_000, "duration": 3_000_000}]
        self.assertEqual(speech_window(events), (0.1, 0.8))
        self.assertEqual(speech_window([]), (None, None))


if __name__ == "__main__":
    unittest.main()


class GuardTests(unittest.TestCase):
    def test_times_outside_audio_do_not_cut_speech(self):
        data = frame() * 20   # 0.48 s
        self.assertEqual(trim_segment(data, 0.1, 5.0), data)
