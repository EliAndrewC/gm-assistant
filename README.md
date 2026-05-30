Podman command for kicking off this project in a container:

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
    --volume "$(pwd)":/workspace:Z \
    --volume /home/eli/l7r:/host-l7r-repo:Z \
    --workdir /workspace \
    --memory 8g \
    --memory-swap 8G \
    --publish 8080 \
    docker.io/docker/sandbox-templates:claude-code \
    bash
```
