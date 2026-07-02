# Contract: `synthesize` AJAX endpoint

A chargen route mirroring the existing `generate_art` portrait endpoint, exposed via the `@ajax` decorator in `chargen/website.py`.

## Request

- Method: POST (the `@ajax` pattern), same delivery shape as `art_prompt` / `generate_art`.
- Parameters:
  - character data fields for the currently displayed character (the same payload the portrait flow already sends), used to build the `CHARACTER` block.
  - `extra_notes` (string, optional): GM steering text. Empty/absent means no steering.
- Re-roll: simply call the endpoint again; each call is independent and fresh.

## Response

JSON (the `@ajax` decorator's envelope):

- Success:
  ```json
  { "ok": true, "backstory": "<1 to 3 paragraphs of prose>" }
  ```
- Failure (HTTP-level handling per the existing `@ajax` convention), with a human-readable message:
  ```json
  { "ok": false, "error": "Gemini API key not configured. ..." }
  ```

Failure cases that MUST be reported (not silently degraded - FR-010):
- Missing/invalid text-model credential.
- Model call error or timeout.
- Missing bundled corpus (deployment artifact built without the snapshot).
- Empty model output (treated as failure; the GM can re-roll).

## Behavioral guarantees

- The prompt sent to the model is the full-corpus brief (FR-002) wrapped by the existing `INSTRUCTIONS` + the character sheet; the honor model and calendar date-anchoring instruction are present (FR-004).
- The model id is the configured `[gemini] text_model` (default `gemini-3.1-pro-preview`), changeable via config without code edits (FR-003).
- Output is the model's text, stripped; the endpoint does not post-process voice/lore.

## Test contract (fixtures, not transport mocks)

- `build_prompt` / `brief.build_full_brief`: tested directly, no network, asserting structure and the equivalence-to-`full` property (FR-009).
- `synthesize`: tested by substituting the client's `generate_content` with a **saved real response fixture** under `chargen/fixtures/`, asserting prompt assembly and stripped-text return (FR-011, Principle X.5).
- Route handler: thin glue; its success/error envelope is exercised by calling the handler with the fixture-backed `synthesize` and with an injected failure, asserting the `ok`/`error` shape.
