# Research: Shrine Builder

Phase 0 for feature 216. The short, durable version of this lives with the catalog in
`webapp/l7r/shrines/CLAUDE.md` (FR-016); this file keeps the search trail.

## R1. Are unstaffed shrines a real thing?

**Yes, and they are the common case, not the exception.** The Kokugakuin *Encyclopedia of Shinto*
entry on *kenmusha* (a shrine with no priest of its own, served by a priest from another shrine)
reasons that the Association of Shinto Shrines' ~79,000 member shrines against ~20,600 registered
priests means at least ~59,000 shrines are jointly administered. Day-to-day care falls to
associations of parishioners (*ujiko*) and devotees. Below that tier are *hokora*: very small
shrines at roadsides and in forests, sometimes no bigger than a birdhouse, kept by the local
community. Offering boxes (*saisen-bako*) are slatted, locked wooden boxes, standard at shrines of
every size. The anime image (a small hall in the woods, a box, a bell rope, nobody there) is
accurate.

- https://d-museum.kokugakuin.ac.jp/eos/detail/?id=9687 (kenmusha)
- https://en.wikipedia.org/wiki/Saisen

**Decision:** the catalog describes exactly this kind of shrine (FR-002a): no living quarters, no
office. A worship pavilion is allowed; lodging is not.

## R2. Enshrining a person whose death was contested

*Goryo shinko*: the spirits of the wronged dead were enshrined as kami so they would be calmed.
Kamigoryo Shrine (794, Prince Sawara) and Sugawara no Michizane (enshrined as Tenjin after
disasters were blamed on him) are the classic cases; *goryo-e* festivals with entertainment were
another way of pacifying such spirits.

- https://en.wikipedia.org/wiki/Gory%C5%8D

**Decision:** this is the in-world reason a magistrate pays for a shrine to a man who died during
a bounty collection, and it is why the consecration category offers a pacification festival as its
own form, not just a "bigger" rite.

## R3. Distinct forms (FR-003)

- **Sanctuary forms.** *Nagare-zukuri* (roof extends forward over the steps as a porch; the most
  common style in Japan, honden usually 1 to 3 bays), *kasuga-zukuri* (small, entered on the gable
  end, curved roof, usually painted; second most common), *shinmei-zukuri* (straight roof, raised
  floor, storehouse ancestry, Ise; traditionally thatched and unpainted). Older still: no building
  at all, a sacred tree or rock (*himorogi*, *iwakura*) bound with rope; Omiwa Shrine has a worship
  hall and NO sanctuary, the mountain itself being the sacred object. And the *hokora*.
- **Roofs.** Thatch, cypress bark (*hiwadabuki*), wooden shingles (*kokera*), copper sheet. The
  Tama records (R4) show copper sheet and copper nails bought in Edo for a village honden.
- **Guardians.** Komainu pairs (one open-mouthed, one closed); foxes at Inari shrines; the earliest
  komainu were wooden and stood inside.
- **Altar.** Offerings are set on an eight-legged unpainted wooden table (*hassokuan*) or on
  *sanbo* stands; outdoor small shrines often have a stone offering slab. (General knowledge,
  consistent with the forms above.)

- https://en.wikipedia.org/wiki/Nagare-zukuri
- https://www.worldhistory.org/Shinto_Architecture/

## R4. Costs

The only itemized village ledgers found: an OCR of an Architectural Institute of Japan
paper (No. 420, Feb 1991) on the Yoshino headman's papers, Tama district, Musashi province.

| work | year | spent | notes |
|---|---|---|---|
| Kasuga Shrine honden (1-bay nagare, bay 7.8 shaku: "large for a one-bay shrine"): copper re-roofing, new bargeboards and gable pendants | 1749 | ~43 ryo 1 bu | materials 53% (copper sheet and nails bought in Edo), craftsmen 15%, rice 12%, ridge-raising and transfer rites 20% |
| Same honden: carved front transoms and polychrome painting | 1805 | ~61.7 ryo | carpenters and painters' labor 44%, materials 16%, rice 11%, fence and ceremonies 21% |
| Konpira Shrine honden (1-bay nagare, bay 4.2 shaku, "small"): minor repair, repair of its cover-shed, repainting | 1764-70 | ~9.5 ryo | labor and workers' rice 66%, materials 29% |
| Myoko-in temple main hall, new (six-room plan, much larger than any honden) | Tenpo era | ~250 ryo (122 ryo = 48% of income) | plus several days of unpaid village labor |

Funding came from four parish villages plus small sums from neighbors, timber sales from the
shrine's own woods, and interest on a village building fund.

For scale: a large city shrine's honden (Kawagoe Hikawa, 1842-49) cost 1,369 ryo excluding its
roof; Asakusa's parishioners took four years to raise 100 ryo for three portable shrines (1772).
A craftsman earned roughly 1 ryo per 30-40 working days.

- https://www.jstage.jst.go.jp/article/aijax/420/0/420_KJ00004076677/_pdf
- https://note.com/kawagoe_hikawa/n/n46255682a738
- https://ffa-edo.com/en/yomimono/bunka/ichiryo-ikura

**Conversion: 1 ryo = 1 koku.** Both are pinned to rice. L7R's koku is "the rice to feed a man for
a year" (`setting/economics.md`), the Edo koku is the same volume of rice, and the Edo rice price
hovered around one ryo per koku. The point of the conversion is relative cost, which it keeps.

**Calibration that follows:** copper re-roofing a LARGE one-bay sanctuary is ~40 koku, so ~22 for
a small one; carving plus polychrome on a large one ~50-60, so ~20 for full carving on a small one.
A plain new small sanctuary is then a few carpenter-months (14-16 koku with materials and food). A
"fairly nice" small forest shrine with a worship pavilion, wooden torii, stone guardians and
lanterns lands around 100-120 koku at the default remoteness.

**Not found:** an Edo price for a stone torii, a komainu pair or a stone lantern. Those are priced
from stonemason labor plus porterage and flagged as estimates in the catalog.

## R5. The negotiation formula

L7R Commerce has no pricing formula (`rules/02-skills.md`: open roll for information or an
unopposed argument, contested if someone argues back). The only price formula in the rules is the
Culture gift rule: spend X% less, X = roll minus 25 (minimum 0). **Decision:** each contract's
saving is max(0, roll minus baseline) percent, baseline 25 by default, and the GM may set the
baseline to a contractor's contested Commerce roll instead.

## R6. Default budget

Tadashi already won the budget negotiation by more than 10 (two raises). **Decision:** the
suggested budget is the fair price of a "fairly nice" reference design at the default remoteness,
plus 20%, rounded up to 5 koku - computed from the catalog, not hard-coded, so it moves with the
prices. The GM can type over it.

## R7. Remains, heads, and a deified person's tomb (amendment 3)

- **Shrine and tomb together, kept apart.** Death pollutes (*kegare*), so a shrine does not hold
  remains; when a person is deified the spirit is enshrined and the body rests in a tomb set apart.
  Tokugawa Ieyasu, deified at Nikko Toshogu, lies in a bronze pagoda-shaped tomb (*hoto*) in the
  Okumiya, up some 200 steps behind the main shrine. Date Masamune's Zuihoden is a mausoleum whose
  occupant is listed as its deity. -> the "heart of the shrine" choice and the inner-tomb option.
  https://eastasia.digitalscholarship.emory.edu/items/show/547 ;
  https://www.nippon.com/en/guide-to-japan/gu900154/
- **Head mounds.** *Kubizuka*: heads of those who died violently were buried under their own
  mound with memorial rites to pacify the spirit; Taira no Masakado's head mound (Otemachi) is
  tied to Kanda Myojin, where he is a deity. Heads of named warriors were salted (*shiozuke*) for
  transport after the head inspection. -> the head step, and the GM's salted head is accurate.
  https://en.wikipedia.org/wiki/Kubizuka ; https://northernearth.co.uk/taira-no-masakado-rebel-god-of-tokyo/
- **Dividing remains (*bunkotsu*).** Takeda Shingen's remains went to Erin-ji, Koyasan and
  Myoshin-ji; Koya hijiri carried portions of the dead to Koyasan; the Buddha's relics were split
  among eight kingdoms. -> the "sharing the remains" step, including the Temple of Ebisu.
  https://ohakakiwame.jp/column/memorial-service/great-man-grave-takeda-shingen.html
- **Washing bones (*senkotsu*).** In Okinawa (from southern Chinese practice) leftover flesh was
  removed by hand and the bones washed with sake before going into an urn. -> "washed clean".
  https://samurai-archives.com/wiki/Okinawan_tombs
- **Bone-gathering (*kotsuage*).** Bones survive cremation and are picked into an urn with
  chopsticks, feet first and skull last; a low village pyre leaves even more. -> "gathered bone by
  bone", and the GM's expectation that bones and tissue remain is right.
- **Relics shown.** From the Heian period, pagoda-shaped reliquaries (*sharito*) holding the ashes
  of revered priests were displayed for veneration; relic halls (*shariden*) such as Toshodaiji's
  hold founders' relics. -> "one bone in a reliquary" and the "remains at the heart" option.
  https://projects.mcah.columbia.edu/jaanus/record/bussharito
- **Graves.** Five-ring stone pagodas (*gorinto*) became common grave markers from the Heian
  period. https://onmarkproductions.com/html/5-elements-pagoda-gravestone.html
- **Boiling the body (mos teutonicus): not found** in Japanese or Chinese practice; excluded
  (FR-031). Washing is the attested East Asian way to clean bones.
- **Burakumin** are the setting's cremators and handle the dead (`l7r.md`, castes), so retrieval
  and preparation are a burakumin contract in the GM ledger.
