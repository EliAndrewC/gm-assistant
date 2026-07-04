# Synthesize Backstory - per-click cost reference

Quick lookup for what one click of "Synthesize Backstory" costs, so it doesn't
have to be recalculated. Covers the model in production
(`gemini-3.1-pro-preview`) and the next-cheaper alternative
(`gemini-3.5-flash`) that a bakeoff previously rejected on quality.

**Measured 2026-07-04**, with 81 campaign characters in context and all three
caste prompts sitting under Gemini's 200k long-context boundary. These numbers
drift up as `l7r.md` grows and the OP cast grows; re-run the script at the
bottom to refresh them. Rates are from Google's pricing page
(<https://ai.google.dev/gemini-api/docs/pricing>).

## Prompt size (tokens)

Per-caste, because the prompt now ships a caste-specific supplement (see the
per-caste section of the webapp `CLAUDE.md`). Both models share the same
Gemini 3.x tokenizer, so the token counts are identical across models.

| Caste             | Prompt tokens |
| ----------------- | ------------: |
| Samurai           |       191,091 |
| Monk              |       147,944 |
| Peasant           |       116,366 |

Output is small and variable: about 2,900 tokens per call (~420 of prose plus
~2,480 of thinking), used as a flat assumption in the cost table below.

## Rate card ($ per 1M tokens)

`gemini-3.1-pro-preview` has a price cliff at a 200k-token prompt; `gemini-3.5-flash`
is flat. All three caste prompts are currently below 200k, so Pro bills at its
cheaper tier - but Samurai has only ~9k tokens of headroom, so watch for corpus
growth pushing it back over (which roughly doubles its input rate).

| Model                     | Input (<=200k) | Input (>200k) | Output (incl. thinking) | Cached input |
| ------------------------- | -------------: | ------------: | ----------------------: | -----------: |
| `gemini-3.1-pro-preview`  |          $2.00 |         $4.00 |   $12.00 / $18.00 (>200k) | $0.20 / $0.40 (>200k) |
| `gemini-3.5-flash`        |          $1.50 |         $1.50 |                   $9.00 |        $0.15 |

Output rate for Pro also follows the 200k tier ($12 under, $18 over). Only
implicit caching is used (automatic, no storage billing, short-lived); see the
"caching" notes in `MEMORY.md` / webapp `CLAUDE.md`.

## Per-click cost

"Cold" = a fresh prompt with nothing cached. "Warm" = a re-roll or the next
click in a burst, where the shared prompt prefix is served from the implicit
cache (only the per-character tail and the output bill at full rate). At current
sizes, a warm click's cost is dominated by output, not input.

| Caste   | 3.1-pro cold | 3.1-pro warm | 3.5-flash cold | 3.5-flash warm |
| ------- | -----------: | -----------: | -------------: | -------------: |
| Samurai |        $0.42 |        $0.07 |          $0.31 |          $0.06 |
| Monk    |        $0.33 |        $0.06 |          $0.25 |          $0.05 |
| Peasant |        $0.27 |        $0.06 |          $0.20 |          $0.04 |

## Should we switch to Flash to save money?

Not for cost alone. After the prompt-trimming work, the whole spread across both
models and all three castes fits between $0.20 and $0.42 cold and $0.04-$0.07
warm - switching Pro to Flash saves only ~$0.10 on a cold click and a cent or
two warm. The synthesis prompt is locked to Pro because a bakeoff found Flash
(then 3.1 Flash) villainized low-honor characters; `gemini-3.5-flash` postdates
that test, so revisiting it would be a quality decision (re-test a handful of
low-honor samples), not a cost one. Given the tiny delta, staying on Pro is the
default.

## Regenerating this table

From `/gm-assistant/webapp/`, with the Gemini API key configured:

```python
python3 - <<'EOF'
import l7r
from chargen import synthesis, opcache, brief

snapshot, recent, n = opcache.get_campaign_context()
base = synthesis.load_brief()
client = synthesis._get_client()
OUT = 2900  # representative output tokens (prose + thinking)

RATES = {
    'gemini-3.1-pro-preview': dict(inp=2.0, out=12.0, cached=0.20),  # <=200k tier
    'gemini-3.5-flash':       dict(inp=1.5, out=9.0,  cached=0.15),
}
castes = [('Samurai', synthesis.SAMPLES[0], 'Samurai'),
          ('Monk',    synthesis.SAMPLES[3], 'Monk'),
          ('Peasant', synthesis.SAMPLES[0], 'Peasant')]

print(f'cast in context: {n}')
for label, char, ctype in castes:
    supp = brief.build_caste_supplement(ctype)
    prompt = synthesis.build_prompt(char, brief=base, campaign_context=snapshot,
                                    caste_supplement=supp, campaign_context_recent=recent)
    t = client.models.count_tokens(model='gemini-3.1-pro-preview', contents=prompt).total_tokens
    out = f'{label:8s} {t:>8,} tok'
    for model, r in RATES.items():
        cold = t*r['inp']/1e6 + OUT*r['out']/1e6
        warm = t*r['cached']/1e6 + OUT*r['out']/1e6
        out += f'   {model}: cold ${cold:.3f} warm ${warm:.3f}'
    print(out)
EOF
```

`count_tokens` is free; this makes no billable generation call. If any caste
prompt crosses 200k, bump that model's `inp`/`out`/`cached` to the `>200k` tier
in `RATES` before reading the cost.
