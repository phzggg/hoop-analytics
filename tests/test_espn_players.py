import ast
import json
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.ingestion.stage_espn_players import SUMMARY_URL, collect_boxscores


def response(payload):
    result = Mock()
    result.json.return_value = payload
    return result


class PlayerCollectionTests(unittest.TestCase):
    def test_collects_only_completed_games_and_preserves_summary(self):
        scoreboard = {"events": [
            {"id": "1", "status": {"type": {"state": "post"}}},
            {"id": "2", "status": {"type": {"state": "pre"}}},
        ]}
        summary = {"boxscore": {"players": [{"team": {"id": "3"}}]}}
        http = Mock()
        http.get.side_effect = [response(scoreboard), response(summary)]

        batch, records = collect_boxscores(date(2026, 1, 15), 1, http)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["batch_id"], batch)
        self.assertEqual(records[0]["game_id"], "1")
        self.assertEqual(records[0]["game_date"], "2026-01-15")
        self.assertEqual(json.loads(records[0]["payload"]), summary)
        self.assertEqual(http.get.call_args_list[1].args[0], SUMMARY_URL)

    def test_rejects_missing_player_boxscore(self):
        scoreboard = {"events": [{"id": "1", "status": {"type": {"state": "post"}}}]}
        http = Mock()
        http.get.side_effect = [response(scoreboard), response({"boxscore": {}})]
        with self.assertRaisesRegex(ValueError, "Box score de jogadores ausente"):
            collect_boxscores(date(2026, 1, 15), 1, http)

    def test_fetches_a_game_only_once_if_it_appears_on_two_scoreboards(self):
        scoreboard = {"events": [{"id": "1", "status": {"type": {"state": "post"}}}]}
        summary = {"boxscore": {"players": [{"team": {"id": "3"}}]}}
        http = Mock()
        http.get.side_effect = [response(scoreboard), response(scoreboard), response(summary)]

        _, records = collect_boxscores(date(2026, 1, 15), 2, http)

        self.assertEqual(len(records), 1)
        self.assertEqual(http.get.call_count, 3)

    def test_rejects_unknown_game_status(self):
        http = Mock()
        http.get.return_value = response({"events": [{"id": "1"}]})
        with self.assertRaisesRegex(ValueError, "status reconhecido"):
            collect_boxscores(date(2026, 1, 15), 1, http)

    def test_rejects_period_without_completed_games(self):
        http = Mock()
        http.get.return_value = response({"events": []})
        with self.assertRaisesRegex(ValueError, "Nenhum jogo finalizado"):
            collect_boxscores(date(2026, 1, 15), 1, http)


class SemanticModelRefreshTests(unittest.TestCase):
    def setUp(self):
        source = (Path(__file__).parents[1] / "notebooks" / "gold" / "16_ESPN_Players_Gold.py").read_text(
            encoding="utf-8"
        )
        function = next(
            node for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef) and node.name == "refresh_semantic_model"
        )
        notebookutils = SimpleNamespace(
            runtime=SimpleNamespace(context={"currentWorkspaceId": "workspace"}),
            credentials=SimpleNamespace(getToken=Mock(return_value="test-token")),
        )
        namespace = {"notebookutils": notebookutils}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<notebook>", "exec"), namespace)
        self.refresh = namespace["refresh_semantic_model"]
        self.session = Mock()

    def test_waits_until_refresh_completes(self):
        model_list = response({"value": [{"name": "NBA Player Analysis", "id": "model"}]})
        pending = response({"status": "Unknown"})
        completed = response({"status": "Completed"})
        self.session.get.side_effect = [model_list, pending, completed]
        self.session.post.return_value = Mock(headers={
            "x-ms-request-id": "d0e99488-1946-478e-9664-44a2ae2d4117"
        })

        with patch("requests.Session", return_value=self.session), patch("time.sleep") as sleep:
            self.refresh()

        self.assertEqual(self.session.post.call_count, 1)
        self.assertEqual(self.session.get.call_count, 3)
        self.assertEqual(
            self.session.get.call_args.args[0],
            "https://api.powerbi.com/v1.0/myorg/groups/workspace/datasets/model/refreshes/"
            "d0e99488-1946-478e-9664-44a2ae2d4117",
        )
        sleep.assert_called_once_with(10)

    def test_rejects_missing_or_ambiguous_model_without_triggering_refresh(self):
        model = {"name": "NBA Player Analysis", "id": "model"}
        for models in ([], [model, model]):
            with self.subTest(count=len(models)):
                self.session.get.return_value = response({"value": models})
                with patch("requests.Session", return_value=self.session):
                    with self.assertRaisesRegex(ValueError, f"encontrados {len(models)}"):
                        self.refresh()
                self.session.post.assert_not_called()

    def test_surfaces_failed_refresh(self):
        self.session.get.side_effect = [
            response({"value": [{"name": "NBA Player Analysis", "id": "model"}]}),
            response({"status": "Failed", "messages": ["refresh error"]}),
        ]
        self.session.post.return_value = Mock(headers={
            "x-ms-request-id": "d0e99488-1946-478e-9664-44a2ae2d4117"
        })
        with patch("requests.Session", return_value=self.session):
            with self.assertRaisesRegex(RuntimeError, "Failed.*refresh error"):
                self.refresh()

    def test_times_out_if_refresh_never_finishes(self):
        self.session.get.return_value = response({
            "value": [{"name": "NBA Player Analysis", "id": "model"}]
        })
        self.session.post.return_value = Mock(headers={
            "x-ms-request-id": "d0e99488-1946-478e-9664-44a2ae2d4117"
        })
        with patch("requests.Session", return_value=self.session), patch(
            "time.monotonic", side_effect=[0, 661]
        ):
            with self.assertRaisesRegex(TimeoutError, "Tempo esgotado"):
                self.refresh()


if __name__ == "__main__":
    unittest.main()
