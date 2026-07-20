Assorted skills, scripts, writeups, and webapps for helping GM my [L7R](https://github.com/EliAndrewC/l7r) game.

Use `./scripts/launch-container.sh` to start or attach to this project's container.  It starts the container detached (`sleep infinity` as PID 1) and opens every terminal as a `podman exec` shell, so exiting any one terminal - including the first - never stops the container or kills the other shells; the container persists until `--fresh` or `podman rm -f`.
