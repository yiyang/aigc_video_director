import json
import shutil
import subprocess
import tempfile
import unittest

from utils import merge_videos_ffmpeg, plan_segment_durations
from video_generator import ensure_no_text_prompt


class TestDurationPlanner(unittest.TestCase):
    def test_manju_prefers_more_cuts(self):
        n, durations, total = plan_segment_durations(
            target_total_sec=30,
            tolerance_sec=2,
            allowed_durations=[4, 5],
            min_duration_sec=4,
            max_segments=10,
            prefer_more_cuts=True,
        )
        self.assertEqual(n, len(durations))
        self.assertEqual(total, sum(durations))
        self.assertTrue(28 <= total <= 32)
        self.assertTrue(all(d in (4, 5) for d in durations))
        self.assertTrue(all(d >= 4 for d in durations))

        # For 30s target, prefer_more_cuts should pick 7 shots (2*5 + 5*4 = 30)
        self.assertEqual(n, 7)
        self.assertEqual(total, 30)
        self.assertEqual(durations.count(5), 2)

    def test_movie_prefers_fewer_cuts(self):
        n, durations, total = plan_segment_durations(
            target_total_sec=30,
            tolerance_sec=2,
            allowed_durations=[4, 5],
            min_duration_sec=4,
            max_segments=10,
            prefer_more_cuts=False,
        )
        self.assertEqual(n, len(durations))
        self.assertEqual(total, sum(durations))
        self.assertTrue(28 <= total <= 32)
        self.assertTrue(all(d in (4, 5) for d in durations))

        # For 30s target, prefer_fewer_cuts should pick 6 shots (6*5 = 30)
        self.assertEqual(n, 6)
        self.assertEqual(total, 30)
        self.assertEqual(durations.count(5), 6)

    def test_non_exact_target_still_in_band(self):
        _, durations, total = plan_segment_durations(
            target_total_sec=31,
            tolerance_sec=1,
            allowed_durations=[4, 5],
            min_duration_sec=4,
            max_segments=10,
            prefer_more_cuts=True,
        )
        self.assertTrue(30 <= total <= 32)
        self.assertTrue(all(d in (4, 5) for d in durations))

    def test_out_of_reach_target_clamps_to_best_effort(self):
        # max_segments=10 => max_total=50, so target=60 should clamp to 50
        n, durations, total = plan_segment_durations(
            target_total_sec=60,
            tolerance_sec=0,
            allowed_durations=[4, 5],
            min_duration_sec=4,
            max_segments=10,
            prefer_more_cuts=True,
        )
        self.assertEqual(n, 10)
        self.assertEqual(total, 50)
        self.assertTrue(all(d == 5 for d in durations))

    def test_invalid_allowed_durations_raises(self):
        with self.assertRaises(ValueError):
            plan_segment_durations(
                target_total_sec=30,
                tolerance_sec=2,
                allowed_durations=[4, 6],
                min_duration_sec=4,
                max_segments=10,
                prefer_more_cuts=True,
            )


class TestNoTextPrompt(unittest.TestCase):
    def test_empty_prompt_gets_no_text_suffix(self):
        out = ensure_no_text_prompt("")
        self.assertTrue("无文字" in out or "无字幕" in out)
        self.assertFalse(out.startswith("，"))

    def test_existing_no_text_prompt_is_not_duplicated(self):
        s = "电影画面，绝对无文字，纯画面"
        out = ensure_no_text_prompt(s)
        self.assertEqual(out, s)

    def test_missing_no_text_prompt_is_appended(self):
        s = "电影画面，角色奔跑，镜头推进"
        out = ensure_no_text_prompt(s)
        self.assertTrue(out.startswith(s))
        self.assertTrue("无文字" in out or "无字幕" in out)


class TestAudioRetentionIfFfmpegAvailable(unittest.TestCase):
    def _skip_if_no_ffmpeg(self):
        if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
            self.skipTest("ffmpeg/ffprobe not found in PATH")

    def _probe_audio_stream_count(self, path):
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=index",
                "-of",
                "json",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if probe.returncode != 0:
            return 0
        try:
            data = json.loads(probe.stdout or "{}")
            return len(data.get("streams", []) or [])
        except Exception:
            return 0

    def test_merge_keeps_audio_by_default(self):
        self._skip_if_no_ffmpeg()

        with tempfile.TemporaryDirectory() as td:
            seg1 = td + "/seg1.mp4"
            seg2 = td + "/seg2.mp4"
            out = td + "/out.mp4"

            # Two compatible segments with audio (same codecs/params)
            for i, seg in enumerate([seg1, seg2], 1):
                cmd = (
                    "ffmpeg -y "
                    "-f lavfi -i color=c=blue:s=320x240:r=25 "
                    "-f lavfi -i sine=frequency=440:sample_rate=44100 "
                    f"-t 1 -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k {seg}"
                )
                subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            merge_videos_ffmpeg([seg1, seg2], out, target_duration_sec=None)
            self.assertGreaterEqual(self._probe_audio_stream_count(out), 1)

    def test_merge_can_force_no_audio(self):
        self._skip_if_no_ffmpeg()

        with tempfile.TemporaryDirectory() as td:
            seg1 = td + "/seg1.mp4"
            seg2 = td + "/seg2.mp4"
            out = td + "/out_no_audio.mp4"

            for seg in [seg1, seg2]:
                cmd = (
                    "ffmpeg -y "
                    "-f lavfi -i color=c=red:s=320x240:r=25 "
                    "-f lavfi -i sine=frequency=440:sample_rate=44100 "
                    f"-t 1 -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k {seg}"
                )
                subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            merge_videos_ffmpeg([seg1, seg2], out, target_duration_sec=None, force_no_audio=True)
            self.assertEqual(self._probe_audio_stream_count(out), 0)


if __name__ == "__main__":
    unittest.main()
