# /quest-tracker

<img alt="Version" src="https://img.shields.io/badge/Version-0.0.2-orange" />
<img alt="Language" src="https://img.shields.io/badge/Language-Python-blue" />
<img alt="Automation" src="https://img.shields.io/badge/Automation-GitHub%20Actions-black" />

## What does this do?

**quest-tracker** is an automated monitoring system that watches for new quest additions and notifies you via Discord. It continuously compares Discord's quest data against a local database to detect when new quests are released, then sends real-time notifications.

## How it works

The automation follows a simple but effective workflow:

1. **GitHub Actions Trigger** — The `quest-watch.yml` workflow runs on a scheduled interval
2. **Fetch Latest Data** — Pulls the current `quests.json` from [xGustavvo's discord-api-tracker](https://github.com/xGustavvo/discord-api-tracker) repo
3. **Compare Quests** — Compares fetched data against the locally stored `data/known_quests.json` file from the previous run
4. **Detect New Quests** — Looks specifically for **new quest IDs** (not edits to existing quests)
5. **Update & Notify** — When a new quest is found:
   - Saves the new quest ID to the known quests list
   - Sends a Discord webhook notification with the quest details
   - Ready to detect the next new quest on the next run



## Tech Stack

- **Python** — Core logic for quest comparison and webhook delivery
- **YAML** — GitHub Actions workflow configuration
- **Discord Webhooks** — Real-time notifications

## Credits

<img alt="Credits" src="https://img.shields.io/badge/Data%20Source-xGustavvo%20discord--api--tracker%20repo-blue" />

Quest data is sourced from [xGustavvo's discord-api-tracker](https://github.com/xGustavvo/discord-api-tracker) repository.

## Project Structure

```
quest-tracker/
├── quest-watch.yml           # GitHub Actions workflow [ triggered via a cron job ]
├── scripts/
│   └── quest_watch.py        # Main Python script that compares the files
├── data/
│   └── known_quests.json     # Persistent known quests database [ list of released Quest IDs ]
└── README.md                 # This file
```
