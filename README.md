Use [`scripts/launch-container.sh`](scripts/launch-container.sh) to start or attach to this project's container.  It starts the container detached (`sleep infinity` as PID 1) and opens every terminal as a `podman exec` shell, so exiting any one terminal - including the first - never stops the container or kills the other shells; the container persists until `--fresh` or `podman rm -f`.

Legacy hand-written podman command (the old attached `--rm` design, kept for reference; note it dies when its terminal's shell exits, taking any exec'd shells with it):

```
podman run --interactive --tty --rm \
    --name gm-assistant \
    --uidmap 0:1:1000 \
    --uidmap 1000:0:1 \
    --uidmap 1001:1001:64536 \
    --gidmap 0:1:1000 \
    --gidmap 1000:0:1 \
    --gidmap 1001:1001:64536 \
    --env HOME=/home/agent \
    --volume "$(pwd)":/gm-assistant:Z \
    --volume /home/eli/l7r:/host-l7r-repo:Z \
    --volume "$HOME/.claude":/home/agent/.claude:z \
    --volume "$HOME/.claude.json":/home/agent/.claude.json:z \
    --workdir /gm-assistant \
    --memory 8g \
    --memory-swap 8G \
    --publish 8080 \
    docker.io/docker/sandbox-templates:claude-code \
    bash
```
