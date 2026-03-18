# UniTrack — University Progress Tracker
## Kali Linux Edition — 100% Offline, Auto-starts on Boot

---

## Install (run once, needs internet only this one time)

```bash
sudo bash install-kali.sh
```

That's it. After this:
- ✅ Opens automatically in your browser every time Kali starts
- ✅ Works 100% offline — no internet needed ever again
- ✅ Django serves the entire app (backend + frontend) on port 8000
- ✅ SQLite database — data persists across reboots

---

## Access
| | URL |
|--|-----|
| 🌐 App | http://localhost:8000 |
| 🛡️ Admin | http://localhost:8000/admin |

**Default login:** `admin@admin.com` / `admin1234`
(Register a new account from the app for personal use)

---

## Manage the service

```bash
bash unitracker.sh start    # start
bash unitracker.sh stop     # stop
bash unitracker.sh restart  # restart
bash unitracker.sh status   # check if running
bash unitracker.sh logs     # view live logs
bash unitracker.sh open     # open in browser
```

Or with systemctl directly:
```bash
sudo systemctl start unitracker
sudo systemctl stop unitracker
sudo systemctl status unitracker
```

---

## Uninstall

```bash
sudo bash uninstall-kali.sh
```

---

## How it works (offline architecture)

```
Browser → http://localhost:8000
              ↓
        Django (port 8000)
        ├── /api/*        → REST API (JSON)
        ├── /admin/*      → Django admin panel
        └── /*            → Serves pre-built Angular app
                            (no Node.js needed at runtime)
```

The Angular frontend is built once during install into `backend/frontend_dist/`.
Django then serves these static files directly — no Node.js, no npm, no internet needed to run.

---

## Prerequisites (for install only)
- Python 3.10+ (pre-installed on Kali)
- Node.js + npm (installed automatically by the script)
