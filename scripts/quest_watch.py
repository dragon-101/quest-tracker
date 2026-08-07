import json
import os
import sys
from datetime import datetime, timezone

import requests

QUEST_SOURCES = [
    "https://raw.githubusercontent.com/xGustavvo/discord-api-tracker/refs/heads/main/data/quests-01.json",
    "https://raw.githubusercontent.com/xGustavvo/discord-api-tracker/refs/heads/main/data/quests-02.json",
]
FALLBACK_QUEST_URL = "https://raw.githubusercontent.com/xGustavvo/discord-api-tracker/refs/heads/main/quest.json"
RESTRICTIONS_URL = "https://gist.githubusercontent.com/xGustavvo/3d08b7369eb34b50834815fd43176cae/raw"

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

REGION_FLAGS = {
    "AT": "🇦🇹", "AU": "🇦🇺", "BE": "🇧🇪", "BR": "🇧🇷", "CA": "🇨🇦", "CH": "🇨🇭", "CN": "🇨🇳",
    "CZ": "🇨🇿", "DE": "🇩🇪", "DK": "🇩🇰", "ES": "🇪🇸", "FI": "🇫🇮", "FR": "🇫🇷", "HK": "🇭🇰",
    "HU": "🇭🇺", "IE": "🇮🇪", "IN": "🇮🇳", "IT": "🇮🇹", "JP": "🇯🇵", "KR": "🇰🇷", "MX": "🇲🇽",
    "NL": "🇳🇱", "NO": "🇳🇴", "NZ": "🇳🇿", "PL": "🇵🇱", "PT": "🇵🇹", "SE": "🇸🇪", "SG": "🇸🇬",
    "SK": "🇸🇰", "UK": "🇬🇧", "US": "🇺🇸", "VN": "🇻🇳",
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
    quest_lists = [fetch_json(url) for url in QUEST_SOURCES]
    fallback = fetch_json(FALLBACK_QUEST_URL)

    data_map = {}

    for lst in quest_lists:
        if not isinstance(lst, list):
            continue
        for q in lst:
            nq = normalize_quest(q)
            if nq.get("id"):
                data_map[nq["id"]] = nq

    if isinstance(fallback, list):
        for q in fallback:
            nq = normalize_quest(q)
            if nq.get("id"):
                data_map.setdefault(nq["id"], nq)

    return data_map


def load_restrictions():
    try:
        data = fetch_json(RESTRICTIONS_URL)
    except Exception:
        return {}, []
    quests = data.get("quests", []) if isinstance(data, dict) else []
    by_id = {q.get("id"): q for q in quests if q.get("id")}
    return by_id, quests


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


def normalize_regions(regions):
    if isinstance(regions, list):
        return {"type": "include", "list": regions}
    if isinstance(regions, dict):
        return {
            "type": "advanced",
            "include": regions.get("include", []),
            "exclude": regions.get("exclude", []),
        }
    return None


def region_label(code):
    return f"{REGION_FLAGS.get(code, '')} {code}".strip()


def build_embed(quest, restrictions_by_id, restrictions_list):
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

    restriction = restrictions_by_id.get(qid)
    if not restriction or not (restriction.get("regions") or []):
        restriction = next(
            (r for r in restrictions_list if r.get("replacement_id") == qid), None
        )

    fields = [
        {"name": "Starts", "value": to_discord_ts(starts_at), "inline": True},
        {"name": "Expires", "value": to_discord_ts(expires_at), "inline": True},
        {"name": "Reward(s)", "value": reward_text, "inline": False},
        {"name": "Task(s)", "value": task_text, "inline": False},
    ]

    if restriction:
        if restriction.get("show_age_gate"):
            fields.append({"name": "Age Restriction", "value": "🔞", "inline": True})

        if restriction.get("is_global") is False:
            norm = normalize_regions(restriction.get("regions"))
            if norm:
                if norm["type"] == "include" and norm.get("list"):
                    fields.append({
                        "name": "Regions (Include)",
                        "value": ", ".join(region_label(r) for r in norm["list"]),
                        "inline": False,
                    })
                if norm["type"] == "advanced":
                    if norm.get("include"):
                        fields.append({
                            "name": "Regions (Include)",
                            "value": ", ".join(region_label(r) for r in norm["include"]),
                            "inline": False,
                        })
                    if norm.get("exclude"):
                        fields.append({
                            "name": "Regions (Exclude)",
                            "value": ", ".join(region_label(r) for r in norm["exclude"]),
                            "inline": False,
                        })

        if restriction.get("replacement_id") or any(
            r.get("replacement_id") == qid for r in restrictions_list
        ):
            fields.append({"name": "Linked", "value": "🔗", "inline": True})

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
    restrictions_by_id, restrictions_list = load_restrictions()

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
        embeds = []
        for qid in new_ids:
            quest = quests.get(qid)
            if not quest:
                continue
            embeds.append(build_embed(quest, restrictions_by_id, restrictions_list))
        if embeds:
            send_webhook(webhook_url, embeds)
            print(f"Sent notifications for {len(embeds)} new quest(s): {', '.join(new_ids)}")
    else:
        print("No new quests.")

    save_state(current_ids)


if __name__ == "__main__":
    main()