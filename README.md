# /quest-tracker

<img alt="Version" src="https://img.shields.io/badge/Version-0.0.3-orange" />
<img alt="Language" src="https://img.shields.io/badge/Language-Python-blue" />
<img alt="Automation" src="https://img.shields.io/badge/Automation-GitHub%20Actions-black" />

## What does this do?

**quest-tracker** is an automated monitoring system that watches for new quest additions and notifies you via Discord. It continuously compares Discord's quest data (thanks to xGustavvo's JSON file of all Discord Quests) against a local database to detect when new quests are released and then sends them as notifications via a Discord Webhook.

## How it works


1. GitHub Actions Trigger — The `quest-watch.yml` workflow runs on a scheduled interval (every 5 minutes using cron-job.org)
2. Fetch Latest Data — Pulls the current `quests.json` from [xGustavvo's discord-api-tracker](https://github.com/xGustavvo/discord-api-tracker) repo
3. Compare Quests — Compares fetched data against the locally stored `data/known_quests.json` file from the previous run
4. Detect New Quests — Looks specifically for new quest IDs (not edits to existing quests which frequently pop up)
5. Update + Notify — When a new quest is found:
   - Saves the new quest ID to the known quests list
   - Sends a Discord webhook notification with the quest details



## Tech Stack

- **Python** — Core logic for quest comparison and webhook delivery
- **YAML** — GitHub Actions workflow configuration
- **Discord Webhooks** — Real-time notifications on Discord

## Credits

<img alt="Credits" src="https://img.shields.io/badge/Data%20Source-xGustavvo%20discord--api--tracker%20repo-blue" />

Quest data is sourced from [xGustavvo's discord-api-tracker](https://github.com/xGustavvo/discord-api-tracker) repository.
## Updates
Here, significant changes to this repository will be shown.

13.08.2026 > No longer using Github Action's automatic cron job option due to how unreliable it is (takes around 1+ hour) and changed to using cron-job.org instead [ more reliable ] to trigger the YML file.

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
