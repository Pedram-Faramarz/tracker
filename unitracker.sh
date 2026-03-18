#!/bin/bash
# UniTrack service manager
# Usage: bash unitracker.sh [start|stop|restart|status|logs]

CMD="${1:-status}"
case "$CMD" in
  start)
    sudo systemctl start unitracker.service
    echo "✓ UniTrack started → http://localhost:8000"
    ;;
  stop)
    sudo systemctl stop unitracker.service
    echo "✓ UniTrack stopped"
    ;;
  restart)
    sudo systemctl restart unitracker.service
    echo "✓ UniTrack restarted → http://localhost:8000"
    ;;
  status)
    sudo systemctl status unitracker.service
    ;;
  logs)
    tail -f /var/log/unitracker.log
    ;;
  open)
    xdg-open http://localhost:8000
    ;;
  *)
    echo "Usage: bash unitracker.sh [start|stop|restart|status|logs|open]"
    ;;
esac
