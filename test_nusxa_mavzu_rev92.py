"""REV92: bir xil nomli mavzu nusxalari — import nusxa ochmaydi, miya to'g'risini tanlaydi."""
import unittest

from modules.curriculum_scope import text_key


class DashTests(unittest.TestCase):
    def test_long_dash_matches_stored_hyphen(self):
        self.assertEqual(text_key("5-bo‘lim takrori: Sanaymiz 1–5"), text_key("5-bo'lim takrori: sanaymiz 1-5"))
        self.assertEqual(text_key("Hello, friend! 3—4 yosh"), text_key("hello, friend! 3-4 yosh"))


if __name__ == "__main__":
    unittest.main()
