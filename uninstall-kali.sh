#!/bin/bash
# Cleanly removes UniTrack autostart service

echo "[•] Stopping UniTrack service..."
systemctl stop unitracker.service 2>/dev/null || true
systemctl disable unitracker.service 2>/dev/null || true
rm -f /etc/systemd/system/unitracker.service
systemctl daemon-reload

REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo $USER)}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
rm -f "$REAL_HOME/.config/autostart/unitracker.desktop"

echo "[✓] UniTrack service removed."
echo "[!] Your data (db.sqlite3) is kept. Delete the unitracker folder to remove everything."
