# `smalltalk` - what people say to any bot

`voices.py` one level up holds what is OURS: the porpoise, the feud, the Mirumoto grievance. This
package holds the long tail every bot on every server gets asked.

| file | holds |
|---|---|
| `topics.py` | the patterns and their ORDER. Order is content: a specific pattern must precede a general one that would swallow it. |
| `gm.py` | the GM Assistant's replies - dry, put upon, about one line in five illustrated. |
| `sheet.py` | the Character Sheet's replies - eager, earnest, never illustrated. |

## Where the taxonomy came from

Conversational platforms ship prebuilt small-talk intent sets because the questions are so
predictable - Dialogflow ES's agent runs to ~86-100 intents, Azure's chit-chat datasets to ~100
scenarios in five personalities. This follows that shape and adds four clusters those enterprise
lists have no reason to carry: science-fiction robot canon, AI-era jokes, Discord and internet
culture, and tabletop reflexes.

**Only the QUESTIONS were reused, never anyone's answers.** Those sets ship their own response text
under their own terms. Every line here is written for these two bots - the same standard `images.py`
applies to pictures: the taxonomy is the reusable part, the writing is not.

## The rules, and which ones a test can hold

- **At least ten replies per category.** The GM's rule of thumb (*"a dozen different responses for
  each call and response"*), enforced by `test_every_pool_holds_at_least_ten_replies`. That
  assertion used to demand three, which is how a median of four shipped through a green gate. If a
  category cannot support ten, it is probably not a category.
- **The Character Sheet never posts an image.** Swept over every pool by a test.
- **Every image URL comes from `images.py`**, with its license verified and its provenance recorded.
- **No dead patterns, no unreachable pools.** Both directions are tested, because a pool no pattern
  reaches can never be said, and a pattern with no pool falls through to the generic reply - which
  reads as the bot ignoring you, and is invisible from either file alone.
- **TONE IS NOT TESTABLE.** Whether a line is genuinely earnest or genuinely sarcastic is a judgment
  call. Do not try to assert it; follow the voice notes at the top of each file.
- **EVERY REPLY EXPLAINS ITSELF** (GM 2026-08-31). The full standard is in
  [`../lore/CLAUDE.md`](../lore/CLAUDE.md); most of this package already met it, because a joke
  about being a bot needs no setup. The context audit found **17 of the first 253 GM Assistant
  replies** wanting, and sixteen of the seventeen were **one shape**: a bare `he`/`she`/`his` in an
  image caption, standing in for somebody the reader has never met. Four captions leaned on the fox
  of the Kuzunoha print and three on the swordsman of the Musashi print, and none of the seven said
  who either was.
  **The rule that follows: a pronoun in a caption must be paid for by a clause saying what that
  person DID.** The file already contained the fix, applied correctly, in `scorpion#9` - *"She lived
  as somebody else for years and everyone believed her"* - which needs no name at all.
  The other class was not verbal: `beep` pointed at a still picture for a SOUND and `hallucinate`
  pointed at one for a QUANTITY. Rewording cannot fix an image asked to carry a sense it does not
  have; the TEXT has to carry it.

## Adding a category

Add the pattern to `topics.py` **in the right place** - specific before general - then add ten-plus
replies to both `gm.py` and `sheet.py`. The tests will hold you to the count, the image rules and
the reachability; the voice is yours.
