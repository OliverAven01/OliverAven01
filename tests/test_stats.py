import importlib.util
from datetime import date, timedelta
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('stats', Path(__file__).resolve().parents[1] / 'scripts/update_stats.py')
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


class StatsTests(unittest.TestCase):
    def test_calendar_reads_counts_instead_of_color_levels(self):
        parser = stats.CalendarParser()
        parser.feed('<td data-date="2026-11-22" data-level="4" id="a"></td>'
                    '<td data-date="2026-11-23" data-level="0" id="b"></td>'
                    '<tool-tip for="b">No contributions on November 23.</tool-tip>'
                    '<tool-tip for="a">1,200 contributions on November 22.</tool-tip>')
        self.assertEqual([d[1] for d in parser.days()], [1200, 0])

    def test_missing_tooltip_cannot_be_reported_as_zero(self):
        parser = stats.CalendarParser()
        parser.feed('<td data-date="2026-11-23" data-level="4" id="a"></td>')
        with self.assertRaises(ValueError):
            parser.days()

    def test_streak_allows_an_unfinished_current_day(self):
        days = [(date(2026, 11, 20) + timedelta(days=i), n, 0) for i, n in enumerate([1, 2, 3, 0])]
        self.assertEqual(stats.streaks(days), (3, 3))

    def test_a_gap_breaks_the_current_streak(self):
        days = [(date(2026, 11, 18) + timedelta(days=i), n, 0) for i, n in enumerate([1, 2, 3, 0, 0])]
        self.assertEqual(stats.streaks(days), (0, 3))

    def test_calendar_with_a_missing_date_is_rejected(self):
        parser = stats.CalendarParser()
        parser.feed('<td data-date="2026-11-21" data-level="1" id="a"></td>'
                    '<td data-date="2026-11-23" data-level="1" id="b"></td>'
                    '<tool-tip for="a">1 contribution on November 21.</tool-tip>'
                    '<tool-tip for="b">2 contributions on November 23.</tool-tip>')
        with self.assertRaises(ValueError):
            parser.days()


if __name__ == '__main__':
    unittest.main()
