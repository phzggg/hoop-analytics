"""Download public ESPN scoreboards and stage them in Fabric OneLake."""

import argparse
import json
import shutil
import subprocess
import uuid
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

import requests


FABRIC_API = "https://api.fabric.microsoft.com/v1"
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"


def azure_token(resource):
    executable = shutil.which("az")
    if not executable:
        raise RuntimeError("Azure CLI nao encontrado. Instale o Azure CLI e execute az login.")
    result = subprocess.run(
        [executable, "account", "get-access-token", "--resource", resource,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True,
        text=True,
        check=True,
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError(f"Nao foi possivel obter token para {resource}")
    return token


def fabric_items(session, url):
    while url:
        if not url.startswith(FABRIC_API + "/"):
            raise ValueError("URL de continuacao Fabric inesperada")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        yield from data.get("value", [])
        url = data.get("continuationUri")


def find_one(items, display_name):
    matches = [item for item in items if item.get("displayName") == display_name]
    if len(matches) != 1:
        raise ValueError(f"Esperado um item chamado {display_name}, encontrados {len(matches)}")
    return matches[0]


def get_files_url(session, workspace_name, lakehouse_name):
    workspace = find_one(fabric_items(session, f"{FABRIC_API}/workspaces"), workspace_name)
    workspace_id = workspace["id"]
    lakehouse = find_one(
        fabric_items(session, f"{FABRIC_API}/workspaces/{workspace_id}/items?type=Lakehouse"),
        lakehouse_name,
    )
    response = session.get(
        f"{FABRIC_API}/workspaces/{workspace_id}/lakehouses/{lakehouse['id']}",
        timeout=30,
    )
    response.raise_for_status()
    url = response.json()["properties"]["oneLakeFilesPath"].rstrip("/")
    if urlparse(url).scheme != "https":
        raise ValueError("Endereco OneLake inesperado")
    return url


def collect_scoreboards(end_date, days, http=requests):
    if not 1 <= days <= 31:
        raise ValueError("days deve estar entre 1 e 31")
    batch_id = uuid.uuid4().hex
    collected_at = datetime.now(timezone.utc).isoformat()
    records = []
    for offset in range(days - 1, -1, -1):
        game_date = end_date - timedelta(days=offset)
        response = http.get(
            SCOREBOARD_URL,
            params={"dates": game_date.strftime("%Y%m%d"), "limit": 100},
            timeout=(10, 30),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            raise ValueError(f"Resposta ESPN invalida para {game_date}")
        records.append({
            "batch_id": batch_id,
            "collected_at": collected_at,
            "requested_date": game_date.isoformat(),
            "source": "ESPN public scoreboard",
            "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        })
    return batch_id, records


def upload_batch(files_url, token, batch_id, records, http=requests, landing_dir="landing"):
    if landing_dir not in ("landing", "boxscores"):
        raise ValueError("Diretorio de destino desconhecido")
    headers = {"Authorization": f"Bearer {token}", "x-ms-version": "2021-08-06"}
    for directory in ("espn_nba", f"espn_nba/{landing_dir}"):
        response = http.put(
            f"{files_url}/{directory}",
            params={"resource": "directory"},
            headers=headers,
            timeout=30,
        )
        if response.status_code != 409 or response.headers.get("x-ms-error-code") != "PathAlreadyExists":
            response.raise_for_status()

    content = b"".join(
        (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        for record in records
    )
    pending = f"{files_url}/espn_nba/{landing_dir}/{batch_id}.pending"
    destination = f"{files_url}/espn_nba/{landing_dir}/{batch_id}.jsonl"
    create_headers = {**headers, "If-None-Match": "*"}
    response = http.put(pending, params={"resource": "file"}, headers=create_headers, timeout=30)
    response.raise_for_status()
    response = http.patch(
        pending,
        params={"action": "append", "position": 0},
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=content,
        timeout=60,
    )
    response.raise_for_status()
    response = http.patch(
        pending,
        params={"action": "flush", "position": len(content)},
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    response = http.put(
        destination,
        headers={**create_headers, "x-ms-rename-source": urlparse(pending).path},
        timeout=30,
    )
    response.raise_for_status()
    response = http.get(destination, headers=headers, timeout=60)
    response.raise_for_status()
    if response.content != content:
        raise RuntimeError("O arquivo salvo no OneLake difere dos dados enviados")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--lakehouse", default="nba_lakehouse")
    args = parser.parse_args()

    batch_id, records = collect_scoreboards(args.end_date, args.days)
    fabric = requests.Session()
    fabric.headers.update({
        "Authorization": f"Bearer {azure_token('https://api.fabric.microsoft.com')}",
        "x-ms-fabric-skill": "e2e-medallion-architecture",
    })
    files_url = get_files_url(fabric, args.workspace, args.lakehouse)
    destination = upload_batch(files_url, azure_token("https://storage.azure.com"), batch_id, records)
    games = sum(len(json.loads(record["payload"])["events"]) for record in records)
    print(f"Lote {batch_id}: {len(records)} dias, {games} jogos.")
    print(f"Arquivo salvo e verificado: {destination}")


if __name__ == "__main__":
    main()
