"""
Fetch Apex Legends stats for a list of players and export one CSV per player.
Each CSV contains all equipped legend trackers with global/PC ranking.

Setup:
  1. Add your API key to .env: APEX_API_KEY=your_key
  2. Fill in PLAYERS below with Origin/EA usernames
  3. pip install -r requirements.txt
  4. python apex_scrapper.py

Output: one CSV per player in ./stats/
"""

import csv
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["APEX_API_KEY"]
BASE_URL = "https://api.mozambiquehe.re/bridge"
OUT_DIR = Path("stats")

# platform: "PC" (Origin/Steam), "PS4" (PlayStation), "X1" (Xbox)
PLAYERS = [
    ("ChrisGuardian0", "PC"),
    ("Maarbis", "PC"),
    ("Apoulpe", "PC"),
    ("Realoney", "PC"),
]


def fetch_player(name: str, platform: str) -> dict:
    r = requests.get(
        BASE_URL,
        params={"player": name, "platform": platform},
        headers={"Authorization": API_KEY},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def extract_rows(data: dict) -> list[dict]:
    global_info = data.get("global", {})
    account = {
        "level": global_info.get("level"),
        "rank": global_info.get("rank", {}).get("rankName", ""),
        "rank_div": global_info.get("rank", {}).get("rankDiv", ""),
        "rank_score": global_info.get("rank", {}).get("rankScore"),
        "top_percent_platform": global_info.get("rank", {}).get("ALStopPercent"),
        "top_percent_global": global_info.get("rank", {}).get("ALStopPercentGlobal"),
    }

    rows = []
    legends = data.get("legends", {}).get("all", {})
    for legend_name, info in legends.items():
        for tracker in info.get("data", []):
            if tracker.get("name") is None:
                continue
            rank = tracker.get("rank", {}) or {}
            rows.append({
                "legend": legend_name,
                "stat": tracker["name"],
                "value": tracker["value"],
                "top_percent_global": rank.get("topPercent", ""),
                "top_percent_pc": tracker.get("rankPlatformSpecific", {}).get("topPercent", "") if tracker.get("rankPlatformSpecific") else "",
                "level": account["level"],
                "rank": f"{account['rank']} {account['rank_div']}".strip(),
                "rank_score": account["rank_score"],
                "rank_top_percent_pc": account["top_percent_platform"],
                "rank_top_percent_global": account["top_percent_global"],
            })
    return rows


def save_csv(player_name: str, rows: list[dict]):
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"{player_name}.csv"
    fieldnames = [
        "legend", "stat", "value",
        "top_percent_global", "top_percent_pc",
        "level", "rank", "rank_score",
        "rank_top_percent_pc", "rank_top_percent_global",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  saved → {path}  ({len(rows)} trackers)")


def main():
    for name, platform in PLAYERS:
        print(f"{name}...")
        try:
            data = fetch_player(name, platform)
            if "Error" in data:
                print(f"  API error — {data['Error']}")
                continue

            rows = extract_rows(data)
            if rows:
                save_csv(name, rows)
            else:
                print("  no trackers equipped on any legend")
        except Exception as e:
            print(f"  error: {e}")


if __name__ == "__main__":
    main()
