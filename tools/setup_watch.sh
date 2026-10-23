#!/usr/bin/env bash
# One-step setup for the Researcher's /watch video skill (PLAYBOOK.md "Video skill").
# Each scheduled run starts on a fresh cloud machine, so this runs at the start of every run.
# Therm's saved choices: local engine (frames + captions), no speech-to-text fallback, balanced detail.
set -e
command -v yt-dlp >/dev/null 2>&1 || pip install --break-system-packages -q "yt-dlp[default,curl-cffi]"
W=$(dirname "$(find / -path '*/watch/skills/watch/SKILL.md' -not -path '/proc/*' 2>/dev/null | head -1)")
if [ -z "$W" ] || [ "$W" = "." ]; then echo "WATCH NOT AVAILABLE: the watch plugin is not installed in this run"; exit 1; fi
python3 "$W/scripts/setup.py" --engine local >/dev/null
python3 "$W/scripts/setup.py" --backend none --detail balanced >/dev/null
python3 "$W/scripts/setup.py" --check
echo "WATCH READY. W=$W"
echo "Use: python3 \"$W/scripts/watch.py\" \"<video URL or file>\" --question \"<question>\" --out-dir <scratch dir>"
