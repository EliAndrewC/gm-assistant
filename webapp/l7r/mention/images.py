"""Every image the bots can post, what it shows, and the proof it is free.

THE LICENSE RULE, from the GM directly (2026-08-31): *"We should only use freely
available images, never making use of something not legitimately free for this
kind of jokey use."* The informality of the use case is not a license - a joke
bot in a private Discord is exactly where it feels harmless to grab whatever a
search returns, and that is the reasoning this file exists to stop.

The bar for anything added here:

  1. **Public domain by AGE, preferred.** A pre-1929 publication is out of
     copyright everywhere, and unlike a granted permission it cannot be revoked
     or relicensed later. Every image below clears this way.
  2. CC0 is acceptable. CC BY only if the attribution rides along in the message.
  3. The license is VERIFIED at the source, never assumed - Wikimedia Commons
     returns `extmetadata.LicenseShortName`, so it is one API call.
  4. Provenance goes in the comment, and `tests/test_mention.py` pins the URLs,
     so swapping an image is a deliberate change to a test that says all of this
     out loud rather than a one-character edit.

THE USAGE RULE, also the GM's (2026-08-31): *"maybe one out of every five
messages should have an image attached except that every message involving your
pet porpoise should always have an image attached"* - and, crucially, *"the
images themselves do not need to be funny as long as the context in which they
are included are funny... it might be very incongruous to just post a picture of
a street sign. But if you have some funny story attached to it... then that is
fine."*

**So an image is never attached at random.** It belongs to a specific line that
was written to set it up - the text is the joke and the picture is the punchline.
The one-in-five rate is a property of how many pool lines carry an image, not a
dice roll at send time, which is why `tests/test_mention.py` measures the rate
across the pools instead of the engine having a probability in it anywhere.

That is also why each entry below records WHAT IT SHOWS: you cannot write the
setup without knowing the picture.
"""

from __future__ import annotations

#: A harbor porpoise. SHOWS: a single porpoise in profile, an engraved plate.
#: PUBLIC DOMAIN - fig. 1 from "Porpoise", Encyclopaedia Britannica 11th ed.,
#: vol. 22 (1911), p. 105, engraver "R.E.H." Free by age.
PORPOISE = (
    'https://upload.wikimedia.org/wikipedia/commons/6/6a/EB1911_Porpoise_-_Phocaena_communis.jpg'
)

#: SHOWS: a steamboat boiler explosion, bodies and debris in the air, crowd on
#: the quay. PUBLIC DOMAIN - "Scene of the Recent Steamboat Explosion, Bristol",
#: The Illustrated London News, 27 July 1850. Free by age.
#:
#: WHY THIS AND NOT A BURNING LAPTOP. The GM asked for *"an image of, like, a
#: computer catching on fire"*. Commons has no decent freely-licensed photograph
#: of one - the searches return wildfires, scorched outlets and government fire
#: reports, and the few real burning-computer photos are licensed in ways that
#: would need attribution carried in the message. Rather than bend the license
#: rule for a gag, the catastrophe is a Victorian machine disaster, which also
#: matches the engraved register of everything else here.
STEAMBOAT = (
    'https://upload.wikimedia.org/wikipedia/commons/a/a3/'
    'Scene_of_the_Recent_Steamboat_Explosion%2C_Bristol_ILN-1850-0727-0011.jpg'
)

#: SHOWS: Miyamoto Musashi killing a monstrous bat in the mountains of Tanba.
#: PUBLIC DOMAIN - Utagawa Kuniyoshi, before 1861. Free by age.
MUSASHI_BAT = 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Kuniyoshi_Miyamoto_Musashi.jpg'

#: SHOWS: Kidomaru confronting a tengu. PUBLIC DOMAIN - Utagawa Kuniyoshi,
#: circa 1840. Free by age.
KIDOMARU_TENGU = 'https://upload.wikimedia.org/wikipedia/commons/2/22/Kuniyoshi_Kidomaru.jpg'

#: SHOWS: archery practice, several figures, from Hokusai's sketchbooks.
#: PUBLIC DOMAIN - Katsushika Hokusai, Hokusai Manga vol. 6, 1817. Free by age.
ARCHERS = (
    'https://upload.wikimedia.org/wikipedia/commons/2/27/'
    'Archers_%28Kyujutsu%29_by_Katsushika_Hokusai_1817.jpg'
)

#: SHOWS: a samurai drinking sake. PUBLIC DOMAIN - Japanese fine print, 1870,
#: Library of Congress LCCN 2002700054. Free by age.
SAKE_SAMURAI = (
    'https://upload.wikimedia.org/wikipedia/commons/5/54/Sake_o_nomu_samurai_LCCN2002700054.jpg'
)

#: SHOWS: an enormous breaking wave with boats beneath it, Mount Fuji behind.
#: PUBLIC DOMAIN - after Katsushika Hokusai, "The Great Wave off Kanagawa",
#: c. 1831. Free by age.
GREAT_WAVE = 'https://upload.wikimedia.org/wikipedia/commons/0/0d/Great_Wave_off_Kanagawa2.jpg'

#: SHOWS: carp swimming, a long narrow panel. PUBLIC DOMAIN - Katsushika
#: Hokusai. Free by age.
CARP = 'https://upload.wikimedia.org/wikipedia/commons/5/58/Hokusai_Carps.jpg'

#: Everything postable, for the test that pins provenance.
ALL_IMAGES = (
    PORPOISE,
    STEAMBOAT,
    MUSASHI_BAT,
    KIDOMARU_TENGU,
    ARCHERS,
    SAKE_SAMURAI,
    GREAT_WAVE,
    CARP,
)


def attach(text: str, url: str) -> str:
    """A reply with its image. Discord embeds a bare URL on its own line."""
    return f'{text}\n{url}'
