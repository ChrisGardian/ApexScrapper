"""
Find the legend with the best win ratio (wins / games played) for each
player in the list. Uses the unofficial Apex Legends Status API.

Setup:
  1. Register a free API key at https://apexlegendsapi.com/
  2. pip install requests
  3. Fill in API_KEY and PLAYERS below, then run.

Note: per-legend stats are only visible if the player has the relevant
tracker equipped on their in-game banner (Wins, Games Played, etc.).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["APEX_API_KEY"]
BASE_URL = "https://api.mozambiquehe.re/bridge"

# platform: "PC" (Origin/Steam), "PS4" (PlayStation), "X1" (Xbox)
# For PC players, use their Origin/EA account name even if they play on Steam.
PLAYERS = [
    ("YourOriginName", "PC"),
    ("FriendOne", "PC"),
    ("FriendTwo", "PC"),
]


def fetch_player(name: str, platform: str) -> dict:
    r = requests.get(BASE_URL, params={
        "auth": API_KEY,
        "player": name,
        "platform": platform,
    }, timeout=10)
    r.raise_for_status()
    return r.json()


def best_legend_by_win_ratio(player_data: dict):
    """Return (legend_name, ratio, wins, games) for the legend with the
    highest wins/games ratio, or None if no legend has both trackers."""
    legends = player_data.get("legends", {}).get("all", {})
    best = None

    for legend_name, info in legends.items():
        # `data` is the list of equipped trackers for this legend
        trackers = {t["name"].lower(): t["value"] for t in info.get("data", [])}

        wins = next(
            (v for k, v in trackers.items() if "win" in k and "kill" not in k),
            None,
        )
        games = next(
            (v for k, v in trackers.items() if "games played" in k or "matches played" in k),
            None,
        )

        if wins is not None and games:
            ratio = wins / games
            if best is None or ratio > best[1]:
                best = (legend_name, ratio, wins, games)

    return best


def main():
    for name, platform in PLAYERS:
        try:
            data = fetch_player(name, platform)
            if "Error" in data:
                print(f"{name}: API error — {data['Error']}")
                continue

            result = best_legend_by_win_ratio(data)
            if result:
                legend, ratio, wins, games = result
                print(f"{name:20} → {legend:12} {wins}W / {games}G  ({ratio:.1%})")
            else:
                print(f"{name:20} → no Wins+Games trackers equipped on any legend")
        except Exception as e:
            print(f"{name:20} → error: {e}")


if __name__ == "__main__":
    main()