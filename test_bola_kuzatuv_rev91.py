"""REV91: bog'cha kunlik rejasi va ota-onaga hisobot — sof mantiq."""
import unittest
from datetime import datetime, timedelta, timezone

from modules.bola_kuzatuv import active_seconds, daily_limit, idle_reason, live_status, stars_for, tashkent_day

NOW = datetime(2026, 10, 1, 7, 0, tzinfo=timezone.utc)   # Toshkentda 12:00, payshanba


class PlanTests(unittest.TestCase):
    def test_day_changes_at_tashkent_midnight_and_weekend_gets_three(self):
        self.assertEqual(tashkent_day(datetime(2026, 10, 2, 19, 30, tzinfo=timezone.utc)).isoformat(), "2026-10-03")  # 00:30 shanba
        self.assertEqual(daily_limit(tashkent_day(NOW)), 2)
        self.assertEqual(daily_limit(tashkent_day(NOW + timedelta(days=2))), 3)   # shanba
        self.assertEqual(daily_limit(tashkent_day(NOW + timedelta(days=3))), 3)   # yakshanba

    def test_stars(self):
        self.assertEqual([stars_for(0, 0), stars_for(4, 5), stars_for(1, 5), stars_for(0, 5)], [1, 3, 2, 1])

    def test_active_time_is_capped_and_needs_visible_playing_lesson(self):
        self.assertEqual(active_seconds(NOW - timedelta(seconds=30), NOW, True, True), 30)
        self.assertEqual(active_seconds(NOW - timedelta(minutes=10), NOW, True, True), 45)
        self.assertEqual(active_seconds(NOW - timedelta(seconds=30), NOW, False, True), 0)
        self.assertEqual(active_seconds(NOW - timedelta(seconds=30), NOW, True, False), 0)


class IdleTests(unittest.TestCase):
    def row(self, **kw):
        base = {"boshlandi_at": NOW - timedelta(minutes=20), "oxirgi_signal_at": NOW - timedelta(seconds=20), "korinadi": True,
                "yashirildi_at": None, "bosh_since": None, "tugadi_at": None, "ogohlantirish_soni": 0, "ogohlantirildi_at": None}
        base.update(kw)
        return base

    def test_active_child_is_not_reported(self):
        self.assertIsNone(idle_reason(self.row(), NOW))
        self.assertEqual(live_status(self.row(), NOW)["holat"], "darsda")

    def test_left_the_app_for_five_minutes(self):
        r = self.row(korinadi=False, yashirildi_at=NOW - timedelta(minutes=6))
        self.assertEqual(idle_reason(r, NOW), "chiqib_ketgan")
        self.assertIsNone(idle_reason(self.row(korinadi=False, yashirildi_at=NOW - timedelta(minutes=3)), NOW))
        self.assertEqual(live_status(r, NOW), {"holat": "chiqib_ketgan", "daqiqa": 6})

    def test_signal_lost_means_app_closed(self):
        r = self.row(oxirgi_signal_at=NOW - timedelta(minutes=7))
        self.assertEqual(idle_reason(r, NOW), "chiqib_ketgan")

    def test_lesson_paused_on_screen(self):
        r = self.row(bosh_since=NOW - timedelta(minutes=5, seconds=10))
        self.assertEqual(idle_reason(r, NOW), "toxtagan")
        self.assertEqual(live_status(r, NOW)["holat"], "toxtagan")

    def test_one_alert_per_absence_and_at_most_two_per_lesson(self):
        warned = self.row(korinadi=False, yashirildi_at=NOW - timedelta(minutes=9), ogohlantirildi_at=NOW - timedelta(minutes=3), ogohlantirish_soni=1)
        self.assertIsNone(idle_reason(warned, NOW))
        again = self.row(korinadi=False, yashirildi_at=NOW - timedelta(minutes=6), ogohlantirildi_at=NOW - timedelta(minutes=20), ogohlantirish_soni=1)
        self.assertEqual(idle_reason(again, NOW), "chiqib_ketgan")
        self.assertIsNone(idle_reason({**again, "ogohlantirish_soni": 2}, NOW))
        self.assertIsNone(idle_reason({**again, "tugadi_at": NOW}, NOW))


if __name__ == "__main__":
    unittest.main()
