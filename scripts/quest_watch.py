import json
import os
import sys
from datetime import datetime, timezone

import requests

QUEST_URL = "https://raw.githubusercontent.com/xGustavvo/discord-api-tracker/refs/heads/main/quest.json"

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "known_quests.json")

TEST_QUEST_IDS = {
    "1193992107035983872",
    "1417206015245418566",
    "1223393873447878656",
    "1276640451235156082",
    "1483951358322147380",
    "1519474065293967471",
}

TASK_MAP = {
    "WATCH_VIDEO": "Video",
    "WATCH_VIDEO_ON_MOBILE": "Mobile (Video)",
    "PLAY_ON_DESKTOP": "Desktop",
    "PLAY_ON_XBOX": "Xbox",
    "PLAY_ON_PLAYSTATION": "PlayStation",
    "PLAY_ACTIVITY": "Activity",
    "STREAM_ON_DESKTOP": "Desktop (Stream)",
    "win": "Win",
}

REWARD_TYPE_NAMES = {
    1: "Code",
    2: "In-Game",
    3: "Avatar Decoration",
    4: "Orbs",
    5: "Nitro",
}


def fetch_json(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def normalize_quest(q):
    if q.get("config"):
        return q
    messages = q.get("messages") or {}
    return {
        "id": q.get("id"),
        "config": {
            "starts_at": q.get("starts_at"),
            "expires_at": q.get("expires_at"),
            "messages": {
                "quest_name": messages.get("quest_name")
                or messages.get("game_title")
                or "Unknown Quest"
            },
            "task_config_v2": q.get("task_config_v2"),
            "rewards_config": q.get("rewards_config"),
        },
    }


def load_all_quests():
    data = fetch_json(QUEST_URL)
    if not isinstance(data, list):
        return {}

    data_map = {}
    for q in data:
        nq = normalize_quest(q)
        if nq.get("id"):
            data_map[nq["id"]] = nq
    return data_map


def get_rewards(q):
    cfg = q.get("config") or {}
    rc = cfg.get("rewards_config") or {}
    return rc.get("rewards") or cfg.get("rewards") or []


def get_tasks(cfg):
    return (
        (cfg.get("task_config_v2") or {}).get("tasks")
        or (cfg.get("task_config") or {}).get("tasks")
        or {}
    )


def task_name(t):
    ttype = t.get("type") or t.get("event_name")
    if ttype == "ACHIEVEMENT_IN_ACTIVITY":
        return "Achievement (Activity)"
    if ttype == "ACHIEVEMENT_IN_GAME":
        return "Achievement (Game)"
    return TASK_MAP.get(ttype, ttype or "None")


def to_discord_ts(iso, style="R"):
    if not iso:
        return "?"
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return f"<t:{int(dt.timestamp())}:{style}>"
    except Exception:
        return "?"


def build_embed(quest):
    qid = quest["id"]
    cfg = quest.get("config") or {}
    name = (cfg.get("messages") or {}).get("quest_name", "Unknown Quest")
    starts_at = cfg.get("starts_at")
    expires_at = cfg.get("expires_at")

    rewards = get_rewards(quest)
    reward_lines = []
    for r in rewards:
        rname = (r.get("messages") or {}).get("name") or r.get("name")
        rtype = REWARD_TYPE_NAMES.get(r.get("type"), "Reward")
        qty = r.get("orb_quantity")
        line = f"{rname} ({rtype})" if rname else rtype
        if qty:
            line += f" x{qty}"
        reward_lines.append(line)
    reward_text = "\n".join(reward_lines) if reward_lines else "No reward data"

    tasks = get_tasks(cfg)
    task_names = [task_name(t) for t in tasks.values()] if tasks else []
    task_text = " / ".join(task_names) if task_names else "None"

    fields = [
        {"name": "Starts", "value": to_discord_ts(starts_at), "inline": True},
        {"name": "Expires", "value": to_discord_ts(expires_at), "inline": True},
        {"name": "Reward(s)", "value": reward_text, "inline": False},
        {"name": "Task(s)", "value": task_text, "inline": False},
    ]

    return {
        "title": f"🆕 New Quest: {name}",
        "url": f"https://discord.com/quests/{qid}",
        "color": 0x5865F2,
        "fields": fields,
        "footer": {"text": f"Quest ID: {qid}"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def send_webhook(webhook_url, embeds):
    CHUNK = 10
    for i in range(0, len(embeds), CHUNK):
        chunk = embeds[i:i + CHUNK]
        resp = requests.post(webhook_url, json={"embeds": chunk}, timeout=30)
        if resp.status_code >= 300:
            print(f"Webhook error {resp.status_code}: {resp.text}", file=sys.stderr)


def load_state():
    if not os.path.exists(STATE_PATH):
        return None
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return None


def save_state(ids):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, indent=2)
        f.write("\n")


def main():
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("DISCORD_WEBHOOK_URL not set", file=sys.stderr)
        sys.exit(1)

    quests = load_all_quests()
    current_ids = {qid for qid in quests.keys() if qid not in TEST_QUEST_IDS}

    previous_ids = load_state()

    if previous_ids is None:
        # First run: establish baseline only, no notifications for pre-existing quests.
        save_state(current_ids)
        print(f"Baseline created with {len(current_ids)} quests. No notifications sent.")
        return

    previous_ids = set(previous_ids)
    new_ids = current_ids - previous_ids

    if new_ids:
        embeds = [build_embed(quests[qid]) for qid in new_ids if qid in quests]
        if embeds:
            send_webhook(webhook_url, embeds)
            print(f"Sent notifications for {len(embeds)} new quest(s): {', '.join(new_ids)}")
    else:
        print("No new quests.")

    save_state(current_ids)


if __name__ == "__main__":
    main()
