"""Download completed ESPN game box scores and stage them in Fabric OneLake."""

import argparse
import json
from datetime import date

import requests

from src.ingestion.stage_espn_scoreboard import (
    azure_token,
    collect_scoreboards,
    get_files_url,
    upload_batch,
)


SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"


def collect_boxscores(end_date, days, http=requests):
    batch_id, scoreboards = collect_scoreboards(end_date, days, http)
    records = []
    seen = set()
    for scoreboard in scoreboards:
        for game in json.loads(scoreboard["payload"])["events"]:
            game_id = game.get("id")
            state = game.get("status", {}).get("type", {}).get("state")
            if not isinstance(game_id, str) or not game_id or state not in ("pre", "in", "post"):
                raise ValueError("Jogo ESPN sem ID ou status reconhecido")
            if state != "post" or game_id in seen:
                continue
            seen.add(game_id)
            response = http.get(SUMMARY_URL, params={"event": game_id}, timeout=(10, 30))
            response.raise_for_status()
            payload = response.json()
            players = payload.get("boxscore", {}).get("players") if isinstance(payload, dict) else None
            if not isinstance(players, list) or not players:
                raise ValueError(f"Box score de jogadores ausente para o jogo {game_id}")
            records.append({
                "batch_id": batch_id,
                "collected_at": scoreboard["collected_at"],
                "game_id": game_id,
                "game_date": scoreboard["requested_date"],
                "source": "ESPN public game summary",
                "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            })
    if not records:
        raise ValueError("Nenhum jogo finalizado encontrado no periodo solicitado")
    return batch_id, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--lakehouse", default="nba_lakehouse")
    args = parser.parse_args()

    batch_id, records = collect_boxscores(args.end_date, args.days)
    fabric = requests.Session()
    fabric.headers.update({
        "Authorization": f"Bearer {azure_token('https://api.fabric.microsoft.com')}",
        "x-ms-fabric-skill": "e2e-medallion-architecture",
    })
    files_url = get_files_url(fabric, args.workspace, args.lakehouse)
    destination = upload_batch(
        files_url, azure_token("https://storage.azure.com"), batch_id, records,
        landing_dir="boxscores",
    )
    print(f"Lote {batch_id}: estatisticas de {len(records)} jogos finalizados.")
    print(f"Arquivo salvo e verificado: {destination}")


if __name__ == "__main__":
    main()
