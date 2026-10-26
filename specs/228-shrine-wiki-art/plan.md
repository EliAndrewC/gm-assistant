# Plan 228: Shrine builder - Other, description, art, wiki page, old links

## Shape

| piece | where |
|---|---|
| Other (`other_<step>`, `instead_<step>`), legacy key table, `answered()` | `l7r/shrines/catalog.py`, `design.py`, `data/legacy.yaml` |
| Other work contract, `gm_other_<step>`, unpriced count | `data/catalog.yaml`, `pricing.py` |
| visual phrases per option | `data/looks.yaml`, merged by `catalog.load_raw` (missing/stray = CatalogError) |
| image prompt + styles + REST image call | `art.py`, `data/art.yaml` |
| description brief + design text | `describe.py`; the call is `l7r.lookup.gemini.generate` (gains `temperature`) |
| wiki page body / GM notes / parsing / lookup by name | `wiki.py` (pure); OP calls are `chargen.op` passed in |
| routes | `Root.shrines(action)`: `GET /shrines`, `GET /shrines/prompt`, `GET /shrines/wiki`, `POST /shrines/describe`, `POST /shrines/draw`, `POST /shrines/wiki` (the last three signed-in only) |
| runaway guard | `l7r/shrines/guard.py`: per user, sliding hour; 120 descriptions, 60 pictures - far above retrying by hand |
| UI | `templates/shrines.html` (Other block per step, "Picture and description" panel on the last step), `shrines.js`, `shrines.css` |
| frozen links | `tests/shrine_links.txt` (Shizu's first) checked by `tests/test_shrines.py` |

## Decisions

- **No LLM for the image prompt.** Each option's `look` is written once, by hand, for an image model; deterministic,
  testable and free. The player can edit the prompt; the style preamble is added at draw time so a style change never
  discards an edit.
- **Models.** Description: `gemini-3.1-flash-lite` (thinking none; $0.25/$1.50 per M tokens). Picture: the portrait
  model (`[gemini] image_model`, default `chargen.art.DEFAULT_IMAGE_MODEL`), 4:3. Both overridable in
  `[shrines] text_model` / `image_model` of development-secrets.ini. Key: `[gemini] api_key`.
- **The image never touches fly.io storage**: the browser holds the drawn PNG (base64) and sends it back with
  Create/Update; the server checks it decodes as an image (Pillow) and uploads it to OP (`op.upload_image`).
- **Wiki lookup is its own request** (`GET /shrines/wiki`), fired by shrines.js after the page loads; the listing is
  cached 2 minutes in-process and dropped after a create. OP down -> "could not check".
- **Old links**: `parse_design` reads through `upgrade_params`; the route 303-redirects a link with old keys to the
  current spelling (hash is kept by the browser).

## Measurements (2026-10-26, Shizu's design)

- **Description**: `gemini-3.1-flash-lite`, 1,360 prompt tokens, 407 output, 2.0 s: **$0.00095**. Three paragraphs,
  every choice used, no invented buildings.
- **Picture**: `gemini-3.1-flash-image`, ~11 s, 1200x896 JPEG (stored as PNG on OP): **~$0.07** (the portrait rate in
  `chargen/art.py`). Ink and woodblock both drew the rope gate, the stone foxes, the moss, the head mound, the bamboo
  box and the stream. The woodblock picture also drew stone lanterns nobody chose, so the framing now says "show only
  what is listed".
- **The key**: `[gemini] api_key` first came back `API_KEY_INVALID`. The key was fine: the secrets file writes it in
  quotes, ConfigObj (chargen) strips them and configparser (`app._load_secrets`) did not, so the webapp sent the quotes
  too. `_load_secrets` now strips one pair of matching quotes. (A `[shrines] gemini_api_key` workaround briefly existed
  and was removed.)
- **Obsidian Portal**: create (with an upload through `op.upload_image`), read back, update, and delete all worked
  against the live campaign on a throwaway page, "Shrine builder test page delete me", which was then deleted. The two
  test pictures stay in the campaign's file assets (ids 1593656, 1593657).

## Deploy

`make deploy` from `webapp/` in the clone (gate, prepare-deploy, flyctl). Verify on l7r-gm-assistant.fly.dev:
Shizu's link opens with every choice; as GM, Describe, Draw, Create wiki page for Shizu's shrine.
