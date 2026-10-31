# Feature Specification: Mantis Clan names

**Feature Branch**: `232-mantis-names` (no branch - spec directory only)

**Created**: 2026-10-31

**Status**: Draft

**Input**: GM request (verbatim, 2026-10-31): "oh yeah, all Mantis characters have names which are based on Indonesian names e.g. here are a bunch of male names: Irehemu (father of multitudes) [in real life, derived from Abraham], Irahim (variant of Irehemu), Kauri (tree), Mohanda (servant of gods) [in real life, clearly like Mohandes Gandhi), Jamiru (beautiful male), Surama [in real life, derived from Suleiman], Noru (light), Muhama (praised / commendable), Putera (prince), Anaru (fisherman) and here are some female names: Marama (moon / moon goddess), Fatama (Fatima - daughter of the prophet), Amar (gender neutral - immortal/eternal), Mariyamu (Miriam - 'wished-for child'), Jamiko (beautiful female), Latifu (gentle and kind - a male name in gaijin name and a female Mantis name). These would be good examples to write down, and then perhaps you could research some good other names - these are treated as gaijin names by Rokugani and some Mantis even use regular Rokugani names - we should perhaps have some random chance for any given Mantis about whether they have a Rokugani name () and then some other chance of them having a Rokugani name they go by even if it's not their real name (some of them would be just a Rokuganized version and some would just be a nickname or whatever to blend in). So maybe... 20% chance of a Mantis just having a Rokugani name and a 10% chance of them having a MAntis name but their character goes by an unrelated Rokugani name, and a 10% chance they go by a Rokuganized versin of the name, like `Amari` instead of `Amar` since `mar` is not a Rokugani syllable."

**Motivation**: the session that prompted this generated three Mantis NPCs (Shione Chacha, Shione Hochi, Shione Katako) and gave all three ordinary Rokugani names, because the chargen engine draws every samurai's given name from the Rokugani pool regardless of clan.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A generated Mantis gets a Mantis name (Priority: P1)

The GM generates a Mantis Clan samurai (via `/chargen` or the webapp's Generate button). Most of the time the character's given name is a Mantis name - an Indonesian-derived name such as Irehemu or Marama - with its meaning shown the way a Rokugani name's meaning is shown.

**Why this priority**: it is the core of the request ("all Mantis characters have names which are based on Indonesian names"); every Mantis NPC generated today is wrong without it.

**Independent Test**: generate a large number of Mantis samurai and confirm that roughly 80% carry a Mantis given name (60% plain, plus the 20% who go by a Rokugani name but whose real name is Mantis) and every Mantis name comes from the Mantis name list.

**Acceptance Scenarios**:

1. **Given** the Mantis name list, **When** a Mantis samurai is generated and lands in the plain-Mantis-name case, **Then** the character's given name and full name use a Mantis name from the list, and the name-meaning line explains it.
2. **Given** a non-Mantis samurai, monk or peasant, **When** it is generated, **Then** its name is drawn exactly as before (Rokugani pool), with no Mantis names.

---

### User Story 2 - Some Mantis go by a Rokugani name (Priority: P1)

Per the GM's percentages, any generated Mantis has: a 20% chance of simply having a Rokugani name; a 10% chance of having a Mantis name but going by an unrelated Rokugani name to blend in; a 10% chance of going by a Rokuganized form of their Mantis name (Amari for Amar); and otherwise (60%) a plain Mantis name.

**Why this priority**: it is the second half of the explicit request, with the GM's numbers.

**Independent Test**: generate a large sample and confirm each of the four cases appears at its stated rate within statistical tolerance; for the two "goes by" cases, confirm both names are recorded.

**Acceptance Scenarios**:

1. **Given** the 20% case, **When** a Mantis is generated, **Then** the given name is an ordinary Rokugani pool name with its ordinary meaning, and nothing records a separate Mantis name.
2. **Given** the 10% unrelated-alias case, **When** a Mantis is generated, **Then** the character is known (full name, record name) by a Rokugani pool name, and the name-meaning line shows both the Rokugani name they go by and their real Mantis name with its meaning.
3. **Given** the 10% Rokuganized case, **When** a Mantis is generated, **Then** the character is known by the Rokuganized form of a Mantis name (e.g. Amari), the Rokuganized form differs from the Mantis original, consists only of Rokugani syllables, and the original Mantis name and meaning are shown.
4. **Given** the four percentages, **When** the GM wants different odds, **Then** they can be changed in configuration without code changes.

---

### User Story 3 - The GM's examples are written down and the list is extended by research (Priority: P1)

The GM's sixteen example names (ten male, six female, one of them, Amar, gender neutral) are recorded with the GM's meanings and real-life derivations, marked as the GM's own, and the list is extended with researched Indonesian-derived names (with some Polynesian names in the same vein as the GM's Kauri, Marama and Anaru) so that generation has enough variety.

**Why this priority**: "These would be good examples to write down, and then perhaps you could research some good other names".

**Independent Test**: open the Mantis name list and find every GM example with the GM's gloss; count the researched additions; each has a meaning and a real-life source note.

**Acceptance Scenarios**:

1. **Given** the list, **When** it is validated, **Then** every GM example is present with its gloss and a GM-provided marker, and no entry lacks a meaning or a real-life source note.
2. **Given** the list, **When** it is validated, **Then** it holds at least 40 male-usable and 40 female-usable names (gender-neutral names count for both).

---

### Edge Cases

- A Mantis name already used by a campaign character (Irehemu, Putera, Haru, Budi, Agus) must be excluded at pick time exactly as Rokugani names are, including set-distinctness against `avoid` names.
- A Mantis name that is already all-Rokugani syllables (Irehemu, Kauri, Noru) has no distinct Rokuganized form; the Rokuganized case must draw only from names whose Rokuganized form differs.
- Gender-neutral entries (Amar) are eligible for either gender.
- If every eligible Mantis name is excluded, generation falls back to a Rokugani name rather than failing.
- A pinned or hand-supplied name (none exists today for samurai) is unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST hold a Mantis name list alongside the existing name pool, each entry carrying: the name, gender (male / female / neutral), meaning, real-life source note, a Rokuganized form (equal to the name when it is already all-Rokugani syllables), and whether the GM provided it.
- **FR-002**: The list MUST contain all sixteen GM examples with the GM's glosses; the GM's bracketed real-life derivations are kept as source notes, not shown in the in-world meaning.
- **FR-003**: The list MUST be extended by research to at least 40 male-usable and 40 female-usable names, each with a meaning and real-life source; researched names follow the GM's adaptation patterns (final vowels added, Arabic and Sanskrit loans reshaped as in Irehemu, Surama, Jamiru).
- **FR-004**: Every Rokuganized form MUST consist only of Rokugani (Japanese) syllables, checked automatically.
- **FR-005**: When generating a samurai of the Mantis Clan, the engine MUST choose one of four naming cases with the GM's default odds - plain Rokugani name 20%, Mantis name going by an unrelated Rokugani name 10%, Mantis name going by its Rokuganized form 10%, plain Mantis name 60% - and the odds MUST be configurable.
- **FR-006**: The name a character goes by is the name used in their full name (and therefore the record name); in both "goes by" cases the real Mantis name and its meaning MUST appear in the same name-meaning line as the name they go by (spec-fidelity round 1: the GM described a nickname to blend in, not a secret identity; whether an alias should be hidden is offered to the GM as a question, not built).
- **FR-007**: Mantis name picks MUST honor the same campaign-roster exclusion and set-distinctness (`avoid`) rules as Rokugani picks, and fall back to a Rokugani name if nothing eligible remains.
- **FR-008**: Non-Mantis characters' naming MUST be unchanged.
- **FR-009**: The `/chargen` skill documentation MUST state that a Mantis's name may be Mantis, Rokuganized or an alias, so a session writing the backstory uses the recorded real name correctly.
- **FR-010**: The `/name` picker (`pick_name.py`) MUST accept a Mantis option that applies the same four-case odds and the same exclusion rules, and works with `--bank`, `--avoid`, a count and gender; with the peasant flag it still produces Mantis names (a Mantis peasant has a Mantis name).
- **FR-011**: `/synthesize` and `/chargen` MUST pass the Mantis option when building the supporting-cast name bank for a Mantis subject, so a Mantis's invented relatives follow the same naming rule.

### Key Entities

- **Mantis name entry**: name, gender, meaning, source note, Rokuganized form, GM-provided flag.
- **Naming case** of a generated Mantis: rokugani / alias / rokuganized / mantis, with the real Mantis name and meaning when one exists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Over 10,000 generated Mantis samurai, each naming case's observed rate is within 2 percentage points of its configured odds.
- **SC-002**: 100% of the GM's sixteen examples are present with the GM's glosses.
- **SC-003**: 100% of Rokuganized forms pass the Rokugani-syllable check, and every Rokuganized-case character goes by a name different from the Mantis original.
- **SC-004**: Zero change in name distribution for non-Mantis characters (existing tests unchanged and green).

## Assumptions

- The chargen engine applies the odds to Mantis Clan samurai, because its peasants and monks carry no clan; Mantis characters named outside the engine (relatives in a backstory, a Mantis peasant named by hand) are covered through the `/name` Mantis option (FR-010, FR-011).
- The record (Obsidian Portal) name is the name the character goes by, since that is how the PCs know them; the real name is recorded per FR-006.
- Renaming the three Mantis NPCs generated earlier this session is a follow-up action on existing records, not part of the engine feature; it is done after the feature lands.
- The webapp `/names` browsing page and `/api/names` (whose requests carry no clan) are out of scope.

## Review history

- **Round 1 (spec-fidelity): CHANGES REQUIRED.** (1) FR-006 invented a GM-only secret for the alias
  case - the GM described a nickname to blend in; (2) the `/name` skill was put out of scope, though
  `/synthesize` and `/chargen` name a Mantis's relatives through it; (3) Assumptions narrowed "all
  Mantis characters" to engine samurai. All three revised (FR-006, FR-010, FR-011, Assumptions).
- **Round 2 (spec-fidelity): FAITHFUL.**
