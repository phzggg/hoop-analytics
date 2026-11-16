import json
import sys
import unittest
from datetime import date
from unittest.mock import Mock, patch

import requests

from src.ingestion import stage_espn_players, stage_espn_scoreboard
from src.ingestion.stage_espn_scoreboard import collect_scoreboards, upload_batch


class WorkspaceArgumentTests(unittest.TestCase):
    def test_manual_collectors_require_an_explicit_workspace_before_collection(self):
        for module, collector in ((stage_espn_scoreboard, "collect_scoreboards"),
                                  (stage_espn_players, "collect_boxscores")):
            with self.subTest(module=module.__name__), \
                    patch.object(sys, "argv", [module.__name__]), \
                    patch.object(module, collector) as collect, \
                    patch("sys.stderr"):
                with self.assertRaises(SystemExit) as error:
                    module.main()
                self.assertEqual(error.exception.code, 2)
                collect.assert_not_called()


class ScoreboardTests(unittest.TestCase):
    def test_collects_requested_dates_and_preserves_original_payload(self):
        response = Mock()
        response.json.return_value = {"events": [{"id": "123"}]}
        http = Mock()
        http.get.return_value = response

        batch, records = collect_scoreboards(date(2026, 1, 15), 2, http)

        self.assertEqual([r["requested_date"] for r in records], ["2026-01-14", "2026-01-15"])
        self.assertEqual({r["batch_id"] for r in records}, {batch})
        self.assertEqual(json.loads(records[0]["payload"]), {"events": [{"id": "123"}]})
        self.assertEqual(http.get.call_count, 2)

    def test_rejects_missing_events_instead_of_reporting_no_games(self):
        http = Mock()
        http.get.return_value.json.return_value = {}
        with self.assertRaisesRegex(ValueError, "Resposta ESPN invalida"):
            collect_scoreboards(date(2026, 1, 15), 1, http)

    def test_validates_date_window(self):
        for days in (0, 32):
            with self.subTest(days=days), self.assertRaises(ValueError):
                collect_scoreboards(date(2026, 1, 15), days, Mock())

    def test_uploads_to_pending_file_then_checks_published_content(self):
        records = [{"batch_id": "batch", "payload": "{}"}]
        content = (json.dumps(records[0], separators=(",", ":")) + "\n").encode()
        existing = Mock(status_code=409, headers={"x-ms-error-code": "PathAlreadyExists"})
        success = Mock(status_code=201, headers={})
        saved = Mock(status_code=200, content=content)
        http = Mock()
        http.put.side_effect = [existing, success, success, success]
        http.patch.return_value = success
        http.get.return_value = saved

        destination = upload_batch("https://lake.example/ws/lh/Files", "token", "batch", records, http)

        self.assertTrue(destination.endswith("/batch.jsonl"))
        rename = http.put.call_args_list[-1]
        self.assertTrue(rename.kwargs["headers"]["x-ms-rename-source"].endswith("/batch.pending"))
        self.assertEqual(rename.kwargs["headers"]["If-None-Match"], "*")
        self.assertEqual(http.patch.call_count, 2)

    def test_does_not_hide_directory_errors(self):
        response = Mock(status_code=409, headers={"x-ms-error-code": "OtherError"})
        response.raise_for_status.side_effect = requests.HTTPError("conflict")
        http = Mock()
        http.put.return_value = response
        with self.assertRaises(requests.HTTPError):
            upload_batch("https://lake.example/ws/lh/Files", "token", "batch", [], http)

    def test_rejects_unexpected_landing_directory(self):
        http = Mock()
        with self.assertRaisesRegex(ValueError, "Diretorio de destino desconhecido"):
            upload_batch("https://lake.example/ws/lh/Files", "token", "batch", [], http,
                         landing_dir="../other")
        http.put.assert_not_called()


if __name__ == "__main__":
    unittest.main()
