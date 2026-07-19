# Feature Specification: Dreams Section (Webapp)

**Feature Branch**: `011-dreams-section`

**Created**: 2026-07-19

**Status**: Draft

**Input**: User description: "Add a Dreams section to the L7R Toolkit webapp with a player-facing rules & framework page plus a gallery of worked dream-divination example scenes, sourced only from the public pool tier (never the gitignored spoiler tier), and linked from the site nav."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Learn how dream divination works and read a worked example (Priority: P1)

A visitor to the L7R Toolkit opens the Dreams section, reads a plain-language explanation of how dream divination works in this setting (why the gods are always reaching out, why noise and silence are expected, how a sleeper's circumstances shape what they receive, and how the roll resolves), and then opens the one worked example to see the whole apparatus in action - the question the characters faced, the god's leaning, and the tables of dream fragments.

**Why this priority**: This is the entire value of the section on day one - a self-contained page that teaches the framework and shows a single complete, spoiler-safe example. With only this, the section is already useful and shippable.

**Independent Test**: Load the Dreams landing page, read the framework, follow the single example link, and confirm the full example scene renders (question, divine direction, how it is run, the shared bands, the four tables, the 10's menu, and the design notes).

**Acceptance Scenarios**:

1. **Given** a visitor on the Dreams landing page, **When** they read the framework section, **Then** they can see the theology (constant sending, poor receiver, expected noise/silence), the role of attunement, and the roll mechanic (bands, the significant 10 and its lucid point pool, rerolls) - without any GM-authoring material.
2. **Given** a visitor on the Dreams landing page, **When** they click the listed example, **Then** the full example scene renders on its own page.
3. **Given** a visitor viewing the example scene, **When** they read it, **Then** it presents the scene-specific content (the question, the god's direction, the tables of fragments, the design notes) in a readable layout.

---

### User Story 2 - Discover Dreams from the site and browse the gallery (Priority: P2)

A visitor browsing the toolkit finds "Dreams" in the main navigation alongside Relics, Names, and Places, and sees the list of available example scenes with enough of a label to choose one.

**Why this priority**: Discoverability and consistency with the rest of the site. Valuable, but the section can be demonstrated without nav polish.

**Independent Test**: From any page, confirm "Dreams" appears in the primary nav, click it, and confirm the examples list shows each available scene with a title and a short descriptor linking to its page.

**Acceptance Scenarios**:

1. **Given** a visitor anywhere on the site, **When** they look at the primary navigation, **Then** "Dreams" is present alongside the existing sections.
2. **Given** the Dreams landing page, **When** the visitor views the examples list, **Then** each available example shows a title and short descriptor and links to its detail page.

---

### User Story 3 - The gallery grows as public examples are added (Priority: P3)

Over time, more spoiler-safe example scenes are added to the public collection, and each appears in the gallery automatically, without a code change.

**Why this priority**: Sustains the section as a growing reference, but not needed for the first release (which ships with a single example).

**Independent Test**: Add a second public example to the collection, refresh the site's content, and confirm it appears in the gallery and is viewable, with no code change.

**Acceptance Scenarios**:

1. **Given** a new spoiler-safe example added to the public collection, **When** the site's content is refreshed, **Then** the new example appears in the gallery and is viewable with no code change.

---

### Edge Cases

- **Spoiler tier must never appear**: scenes marked as live-campaign spoilers (the local, gitignored tier) must never be listed or reachable through the site, under any URL.
- **No examples yet**: if the public collection is empty, the landing page still shows the framework and an empty (or gracefully worded) examples list rather than breaking.
- **Malformed example**: an example file missing required fields is skipped rather than breaking the gallery or the site.
- **Unknown scene**: requesting an example that does not exist returns a friendly not-found response, not an error page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The site MUST provide a Dreams landing page that presents a player-facing rules & framework explanation of dream divination followed by a list of example scenes.
- **FR-002**: The framework text MUST convey the theology (the gods are always reaching out; the mortal is a poor receiver; noise and silence are expected, not failures), how a sleeper's attunement and circumstances shape the odds, and the core mechanic (the single die roll; the no-dream / noise / meaningful outcome bands; the always-significant highest result and its lucid-dream point pool; and that certain resources let a dreamer reroll).
- **FR-003**: The framework text MUST omit GM-authoring-only material - the storage/spoiler tiers, how to write fragments, and how scenes are authored.
- **FR-004**: The landing page MUST list each available example with a title and a short descriptor, each linking to that example's own page.
- **FR-005**: The site MUST provide a per-example page that renders the full scene: its question, the god's direction, how it is run, the relic choice, the shared bands, the four tables of fragments, the highest-result menu, and the design notes.
- **FR-006**: Example scenes MUST be sourced from the public example collection so that adding a new public example makes it appear without a code change (data-driven).
- **FR-007**: The site MUST NEVER list, load, or render any scene from the live-campaign spoiler tier. Only public, spoiler-safe examples are ever exposed. (This is the load-bearing constraint of the feature.)
- **FR-008**: An example file that is malformed or missing required fields MUST be skipped without breaking the gallery or the site.
- **FR-009**: A request for a non-existent example MUST return a friendly not-found response rather than an error.
- **FR-010**: "Dreams" MUST appear in the site's primary navigation alongside Relics, Names, and Places.
- **FR-011**: The Dreams pages MUST match the site's existing visual style and be responsive across the site's standard viewports with no content clipping or gross layout imbalance.

### Key Entities *(include if feature involves data)*

- **Dream Scene (example)**: a complete, worked, spoiler-safe example of dream divination. Bears a title, the god or spirit consulted, the question the characters faced, the god's leaning ("divine direction"), the mechanic tuning (attunement level, outcome-band proportions), the tables of dream fragments, and provenance/setting notes. Sourced from the public example collection and addressable by a stable, human-readable slug for its URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A visitor with no prior knowledge can, after reading the framework, correctly explain in their own words why some dreamers get no useful dream (noise and silence are expected) - verifiable by review of the framework's clarity.
- **SC-002**: A visitor can go from the site's main navigation to reading a full example scene in at most 2 clicks.
- **SC-003**: Adding a new spoiler-safe example to the public collection makes it appear in the gallery with no code change.
- **SC-004**: Zero spoiler-tier scenes are reachable through the site by any means (list, link, or direct URL).
- **SC-005**: The Dreams pages pass the site's standard UI verification with zero clipping or layout-balance issues across all standard viewports.

## Assumptions

- Public example scenes are stored as structured content files (frontmatter plus body) in the existing public dream-example collection, mirroring how the site's Relics content is stored and loaded.
- The player-facing framework text is a hand-authored adaptation derived from the dream-generation skill's framework, maintained with the feature - not machine-generated from the skill at request time.
- The deployment process makes the public example collection available to the running site through the same content-bundling mechanism the site already uses to ship its other file-based content (the live-campaign spoiler tier is never bundled).
- The first release ships with exactly one example (the Daikoku Masamune-sword scene); the section is designed to hold a growing gallery.
- Because these examples are drawn from concluded (past-campaign) or purely theoretical situations, showing the entire scene - including the design notes - to the public is intentional and safe; the spoiler protection is enforced at the tier boundary (only public examples exist on the site), not by hiding sections within an example.
