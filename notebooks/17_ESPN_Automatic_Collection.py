# Fabric Notebook Code: 17_ESPN_Automatic_Collection
"""Collect ESPN scoreboards and completed player box scores in OneLake."""

import json
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
ROOT = "Files/espn_nba"


def fetch_json(session, url, params):
    for attempt in range(3):
        try:
            response = session.get(url, params=params, timeout=(10, 30))
            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as error:
            if (isinstance(error, requests.HTTPError) and error.response is not None
                    and error.response.status_code < 500 and error.response.status_code != 429):
                raise
            if attempt == 2:
                raise
            print(f"ESPN indisponivel; nova tentativa {attempt + 2}/3: {error}")
            time.sleep(5 * (attempt + 1))


def start_date(season_start, today, checkpoints, season_year):
    matching = []
    prefix = f"{season_year}_"
    for name in checkpoints:
        if name.startswith(prefix) and name.endswith(".done"):
            matching.append(date.fromisoformat(name[len(prefix):len(prefix) + 10]))
    if not matching:
        return season_start
    latest = max(matching)
    if latest > today:
        raise ValueError("Checkpoint ESPN esta em uma data futura.")
    return max(season_start, min(latest - timedelta(days=6), today - timedelta(days=6)))


def collect_day(session, game_date, season_year):
    payload = fetch_json(session, SCOREBOARD_URL, {
        "dates": game_date.strftime("%Y%m%d"), "limit": 100,
    })
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError(f"Placar ESPN invalido: {game_date}")
    batch_id = uuid.uuid4().hex
    collected_at = datetime.now(timezone.utc).isoformat()
    scoreboard = {
        "batch_id": batch_id, "collected_at": collected_at,
        "requested_date": game_date.isoformat(), "source": "ESPN public scoreboard",
        "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    }
    boxscores = []
    seen = set()
    for event in payload["events"]:
        game_id = event.get("id")
        status = event.get("status", {}).get("type", {}).get("state")
        season = event.get("season", {})
        if not isinstance(game_id, str) or not game_id or status not in ("pre", "in", "post"):
            raise ValueError(f"Jogo ESPN com ID ou status invalido em {game_date}")
        if not isinstance(season.get("year"), int) or not isinstance(season.get("type"), int):
            raise ValueError(f"Jogo ESPN sem temporada valida: {game_id}")
        if season.get("year") != season_year or season.get("type") not in (2, 3):
            continue
        if status != "post" or game_id in seen:
            continue
        seen.add(game_id)
        summary = fetch_json(session, SUMMARY_URL, {"event": game_id})
        players = summary.get("boxscore", {}).get("players") if isinstance(summary, dict) else None
        if not isinstance(players, list) or len(players) != 2:
            raise ValueError(f"Box score incompleto para o jogo {game_id}")
        boxscores.append({
            "batch_id": batch_id, "collected_at": collected_at, "game_id": game_id,
            "game_date": game_date.isoformat(), "source": "ESPN public game summary",
            "payload": json.dumps(summary, ensure_ascii=False, separators=(",", ":")),
        })
    return batch_id, scoreboard, boxscores


def write_batch(fs, directory, batch_id, records):
    if not records:
        return
    content = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in records)
    pending = f"{ROOT}/{directory}/{batch_id}.pending"
    target = f"{ROOT}/{directory}/{batch_id}.jsonl"
    if not fs.put(pending, content, False):
        raise RuntimeError(f"Falha ao gravar {pending}")
    if not fs.mv(pending, target, False, False):
        raise RuntimeError(f"Falha ao publicar {target}")


def main(fs):
    for directory in ("landing", "boxscores", "checkpoints"):
        if not fs.mkdirs(f"{ROOT}/{directory}"):
            raise RuntimeError(f"Falha ao criar diretorio {directory}")
    session = requests.Session()
    today = datetime.now(ZoneInfo("America/New_York")).date()
    current = fetch_json(session, SCOREBOARD_URL, {"dates": today.strftime("%Y%m%d"), "limit": 100})
    leagues = current.get("leagues") if isinstance(current, dict) else None
    if not isinstance(leagues, list) or not leagues:
        raise ValueError("Calendario da temporada ESPN indisponivel")
    season = leagues[0].get("season", {})
    season_year = season.get("year")
    if not isinstance(season_year, int) or not isinstance(season.get("startDate"), str):
        raise ValueError("Temporada ESPN sem ano ou data inicial")
    season_start = date.fromisoformat(season["startDate"][:10])
    if season_start > today:
        raise ValueError("A temporada ESPN retornada ainda nao comecou")
    checkpoints = [entry.name for entry in fs.ls(f"{ROOT}/checkpoints")]
    first = start_date(season_start, today, checkpoints, season_year)
    games = 0
    for offset in range((today - first).days + 1):
        game_date = first + timedelta(days=offset)
        batch_id, scoreboard, boxscores = collect_day(session, game_date, season_year)
        write_batch(fs, "landing", batch_id, [scoreboard])
        write_batch(fs, "boxscores", batch_id, boxscores)
        games += len(boxscores)
        print(f"{game_date}: {len(boxscores)} jogos finalizados coletados")
    checkpoint = f"{ROOT}/checkpoints/{season_year}_{today.isoformat()}_{uuid.uuid4().hex}.done"
    if not fs.put(checkpoint, json.dumps({"through": today.isoformat(), "season": season_year}), False):
        raise RuntimeError("Falha ao registrar checkpoint da coleta ESPN")
    print(f"Coleta concluida: {first} a {today}; {games} box scores.")


if __name__ == "__main__":
    main(notebookutils.fs)
