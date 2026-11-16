import importlib.util
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import requests


path = Path(__file__).resolve().parents[1] / "notebooks" / "17_ESPN_Automatic_Collection.py"
spec = importlib.util.spec_from_file_location("espn_fabric_collection", path)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class FabricCollectionTests(unittest.TestCase):
    def test_transient_timeout_is_retried(self):
        response = Mock()
        response.json.return_value = {"events": []}
        session = Mock()
        session.get.side_effect = [requests.Timeout("timeout"), response]
        with patch.object(collector.time, "sleep"):
            self.assertEqual(collector.fetch_json(session, "https://example.test", {}), {"events": []})
        self.assertEqual(session.get.call_count, 2)

    def test_start_date_backfills_and_recovers_long_gaps(self):
        start, today = date(2026, 9, 30), date(2026, 11, 12)
        self.assertEqual(collector.start_date(start, today, [], 2027), start)
        self.assertEqual(
            collector.start_date(start, today, ["2027_2026-10-25_abc.done"], 2027),
            date(2026, 10, 19),
        )
        self.assertEqual(
            collector.start_date(start, today, ["2027_2026-11-11_abc.done"], 2027),
            date(2026, 11, 5),
        )
        self.assertEqual(
            collector.start_date(start, today, ["2026_2026-11-11_abc.done"], 2027),
            start,
        )
        with self.assertRaisesRegex(ValueError, "data futura"):
            collector.start_date(start, today, ["2027_2026-11-13_abc.done"], 2027)

    def test_collects_only_completed_regular_and_postseason_boxscores(self):
        def game(game_id, season_type, state):
            return {"id": game_id, "season": {"year": 2027, "type": season_type},
                    "status": {"type": {"state": state}}}

        payload = {"events": [game("1", 2, "post"), game("2", 1, "post"),
                              game("3", 2, "in"), game("4", 3, "post")]}
        summary = {"boxscore": {"players": [{}, {}]}}
        with patch.object(collector, "fetch_json", side_effect=[payload, summary, summary]):
            _, scoreboard, boxscores = collector.collect_day(Mock(), date(2026, 11, 11), 2027)
        self.assertEqual([row["game_id"] for row in boxscores], ["1", "4"])
        self.assertIn('"id":"2"', scoreboard["payload"])

    def test_incomplete_boxscore_fails_instead_of_advancing(self):
        game = {"id": "1", "season": {"year": 2027, "type": 2},
                "status": {"type": {"state": "post"}}}
        with patch.object(collector, "fetch_json", side_effect=[{"events": [game]}, {"boxscore": {}}]):
            with self.assertRaisesRegex(ValueError, "Box score incompleto"):
                collector.collect_day(Mock(), date(2026, 11, 11), 2027)

    def test_empty_day_is_valid_but_missing_season_is_not(self):
        with patch.object(collector, "fetch_json", return_value={"events": []}):
            _, _, boxscores = collector.collect_day(Mock(), date(2026, 11, 11), 2027)
        self.assertEqual(boxscores, [])
        game = {"id": "1", "status": {"type": {"state": "post"}}}
        with patch.object(collector, "fetch_json", return_value={"events": [game]}):
            with self.assertRaisesRegex(ValueError, "temporada valida"):
                collector.collect_day(Mock(), date(2026, 11, 11), 2027)

    def test_stage_uses_unique_pending_file_then_publishes(self):
        fs = Mock()
        fs.put.return_value = True
        fs.mv.return_value = False
        with self.assertRaisesRegex(RuntimeError, "Falha ao publicar"):
            collector.write_batch(fs, "landing", "batch", [{"x": 1}])
        fs.put.assert_called_once()
        fs.mv.assert_called_once()

    def test_collection_failure_does_not_write_checkpoint(self):
        fs = Mock()
        fs.mkdirs.return_value = True
        fs.ls.return_value = []
        season = {"leagues": [{"season": {"year": 2027, "startDate": "2026-09-30T00:00Z"}}]}
        with patch.object(collector, "datetime") as clock, \
                patch.object(collector, "fetch_json", return_value=season), \
                patch.object(collector, "collect_day", side_effect=ValueError("API incompleta")):
            clock.now.return_value.date.return_value = date(2026, 11, 12)
            with self.assertRaisesRegex(ValueError, "API incompleta"):
                collector.main(fs)
        fs.put.assert_not_called()


if __name__ == "__main__":
    unittest.main()
