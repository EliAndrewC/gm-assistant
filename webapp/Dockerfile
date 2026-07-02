# L7R Toolkit — production image
#
# Pinned to Python 3.13 to match pyproject.toml's requires-python and the
# Python that ships in the dev container. Slim base to keep the layer small.
FROM python:3.13-slim AS base

# System deps: opencv-python-headless and pillow pull in libGL + image codecs.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for layer cache.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY chargen ./chargen
COPY l7r ./l7r
COPY development-defaults.ini ./
# Discord OAuth credentials + whitelist + Gemini/Obsidian creds. The image is
# private to the Fly account; rotating means rebuilding.
COPY development-secrets.ini ./
COPY authorize_op.py ./
# pool data (relic + name pools) lives under /gm-assistant/.claude/skills/<skill>/.
# The image needs both — we lay them out under /app/skills and point the app at them.
COPY skills ./skills
# Bundled setting corpus (l7r.md + budgets.md) for the synthesis prompt;
# brief.py resolves it at /app/setting (no bind-mount in prod).
COPY setting ./setting
# Campaign-character cache (cold-start base; refreshed in-memory at runtime).
COPY opcache ./opcache

ENV PORT=8080
ENV FLY_APP_NAME=l7r-gm-assistant
ENV PYTHONUNBUFFERED=1
ENV L7R_RELIC_POOL_DIR=/app/skills/relic/pool
ENV L7R_NAMES_DIR=/app/skills/name
ENV L7R_PLACES_DIR=/app/skills/place-names

EXPOSE 8080

CMD ["cherryd", "--import", "l7r"]
