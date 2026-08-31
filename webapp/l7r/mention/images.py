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

#: SHOWS: four cats in assorted poses, illustrating Japanese proverbs.
#: PUBLIC DOMAIN - Utagawa Kuniyoshi. Free by age.
CATS = (
    'https://upload.wikimedia.org/wikipedia/commons/1/15/'
    'Kuniyoshi_Utagawa%2C_For_cats_in_different_poses.jpg'
)

#: SHOWS: Kuzunoha, the fox-woman of legend, who lived for years as a human wife
#: before her true shape showed. PUBLIC DOMAIN - Utagawa Kuniyoshi. Free by age.
FOX_WOMAN = 'https://upload.wikimedia.org/wikipedia/commons/c/c6/Kuniyoshi_Kuzunoha.jpg'

#: SHOWS: Yoshitsune and Benkei duelling on Gojo Bridge. PUBLIC DOMAIN - Utagawa
#: Kuniyoshi, 19th century. Free by age.
DUEL_ON_THE_BRIDGE = (
    'https://upload.wikimedia.org/wikipedia/commons/e/ec/'
    'Yoshitsune_and_Benkei%27s_duel_on_Gojo_Bridge%2C_a_scean_of_the_Chronicle_of_'
    'Yoshitsune_%28Gikei-ki%29_-_Heroes_of_China_and_Japan_%28Wakan_Eiyu_Ga-den%29%2C_'
    'Ukiyo-e_print_by_Kuniyoshi_Utagawa%2C_circa_19th_century.jpg'
)

#: SHOWS: "The moon's inner vision", a figure in contemplation under the moon.
#: PUBLIC DOMAIN - Tsukioka Yoshitoshi, One Hundred Aspects of the Moon. Free by age.
INNER_VISION = 'https://upload.wikimedia.org/wikipedia/commons/2/28/Yoshitoshi_-_100_Aspects_of_the_Moon_-_34.jpg'

#: SHOWS: "Rainy moon" - a solitary figure in the rain at night. PUBLIC DOMAIN -
#: Tsukioka Yoshitoshi, One Hundred Aspects of the Moon. Free by age.
RAINY_MOON = 'https://upload.wikimedia.org/wikipedia/commons/8/8d/Yoshitoshi_-_100_Aspects_of_the_Moon_-_78.jpg'

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
    CATS,
    FOX_WOMAN,
    DUEL_ON_THE_BRIDGE,
    INNER_VISION,
    RAINY_MOON,
)

#: WHAT IS ACTUALLY IN EACH PICTURE, in the words a caption would use for it.
#:
#: This exists because of a reply that shipped saying *"It is a fish. You have
#: earned a fish."* with the CATS print attached (`smalltalk/gm.py`, `rickroll`,
#: found by the context audit on 2026-08-31). The reply was not merely
#: unexplained - it was contradicted by its own attachment, and nothing in the
#: suite compares a caption against what the picture shows, because nothing knew
#: what the pictures show.
#:
#: `test_no_caption_describes_a_different_picture` reads this table, so the
#: subject words live in the same file as the URL they belong to and adding an
#: image forces adding them (a second test holds every URL in `ALL_IMAGES` to
#: having an entry here).
#:
#: ONLY WORDS THAT ARE ALWAYS ABOUT THE PICTURE, and the list was trimmed by
#: measurement rather than taste. The first version included `wave`, `moon`,
#: `rain`, `duel`, `bridge`, `sake` and `bow`, and produced four false positives
#: immediately: a caption on the sake print mentioning that the rain did not
#: come, one on the rainy-moon print about a courtier mistaking a greeting for a
#: duel challenge, one on the bridge print naming the Battle of the Cresting
#: Wave. Those are ordinary Rokugani vocabulary and a caption may use them about
#: anything. What is left is nouns for the CREATURE OR OBJECT DEPICTED, which a
#: caption has no other reason to say. An empty set is the right entry for a
#: picture whose subject has no such noun.
SUBJECTS: dict[str, frozenset[str]] = {
    PORPOISE: frozenset({'porpoise'}),
    STEAMBOAT: frozenset({'boiler', 'steamboat'}),
    MUSASHI_BAT: frozenset({'bat'}),
    KIDOMARU_TENGU: frozenset({'tengu'}),
    ARCHERS: frozenset({'archer', 'archers'}),
    SAKE_SAMURAI: frozenset(),
    GREAT_WAVE: frozenset(),
    CARP: frozenset({'carp', 'fish'}),
    CATS: frozenset({'cat', 'cats'}),
    FOX_WOMAN: frozenset({'fox'}),
    DUEL_ON_THE_BRIDGE: frozenset(),
    INNER_VISION: frozenset(),
    RAINY_MOON: frozenset(),
}


def attach(text: str, url: str) -> str:
    """A reply with its image. Discord embeds a bare URL on its own line."""
    return f'{text}\n{url}'
