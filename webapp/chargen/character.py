import re
from os.path import join
from copy import deepcopy
from random import random, randrange, normalvariate, choice

from chargen import config
from chargen import constants as c


def rounded(x: int, minval=1, maxval=15) -> int:
    return min(maxval, max(minval, round(x * 2) / 2))


def unused_name(gender: str = None) -> tuple[str, str]:
    """
    When randomly generating a name, we want to make sure that we don't pick a
    name which is already in use in this campaign.  We maintain a global set of
    existing names and then keep randomly picking a new name until we find one
    which we haven't already used.
    """
    name = None
    gender = gender or choice(['male', 'female'])
    while not name or name in c.USED_NAMES:
        name = choice(list(c.NAMES[gender]))
    return name, c.NAMES[gender][name]


def weighted_choice(d: dict) -> str:
    """
    We have a lot of attributes with weighted options, e.g. when generating a
    character we might pick their school via these options:
        {
            'Bushi': 0.8,
            'Courtier': 0.1,
            'Merchant': 0.1
        }
    This function treats that as 80% chance to pick 'Bushi', and so forth.  If
    the dict of options is empty then we return the empty string; this would be
    the case if e.g. we're trying to pick a House for a Family for which we have
    not defined different houses in our config, etc.
    """
    if d:
        roll = randrange(sum(d.values()))
        total = 0
        for choice, percent in d.items():
            total += percent
            if roll < total:
                return choice
    else:
        return ''


class Character:
    """
    This is the parent class used to generate characters.  It defines
    """

    def __init__(self):
        self.gender = choice(['male', 'female'])
        self.personal_name, self.name_meaning = unused_name(self.gender)

        self.xp = self.gen_xp()
        self.honor = self.gen_honor()
        self.traits = self.gen_traits()
        self.collects = ''
        if 'collector' in self.traits:
            item = choice(c.COLLECTABLES)
            self.collects = item['name']
            self.collects_art = item['art']
            # Replace generic trait with specific one
            self.traits[self.traits.index('collector')] = f'collects {item["name"]}'
        self.tags = self.gen_tags()
        self.id = str(randrange(1e9))

    @classmethod
    def types(cls):
        types = {}
        for subclass in cls.__subclasses__():
            types[subclass.__name__] = subclass
            types.update(subclass.types())
        return types

    def gen_xp(self) -> int:
        """
         A person at their gempukku has on average about 150 XP.  Here's a chart
         showing what percentage of the population has at least a given amount
         of XP or higher:

            100%       0 XP or greater
            ~80%     150 XP or greater
            ~60%     160 XP or greater
            ~50%     170 XP or greater
            ~40%     180 XP or greater
            ~30%     190 XP or greater

            ~20%     200 XP or greater
            ~18%     210 XP or greater
            ~16%     220 XP or greater
            ~14%     230 XP or greater
            ~12%     240 XP or greater

            ~10%     250 XP or greater
            ~1%      300 XP or greater
            ~0.1%    350 XP or greater
            ~0.01%   400 XP or greater
            ~0.001%  450 XP or greater
            ~0.0001% 500 XP or greater

        This method implements that pattern, with the added subtlety that people
        of higher ranks are presumed to have a higher XP baseline.
        """
        base = 0
        for rank, rank_base in config['rank_xp_bases'][self.__class__.__name__].items():
            if self.rank >= int(rank):
                base = rank_base

        while random() < 0.10:
            base += 50
        return base + 5 * randrange(10)

    def gen_honor(self, base=2.0) -> float:
        """
        We presume that higher ranking people are more likely to have a slightly
        honor score, and this implements a normal distribution for that.
        """
        if random() < 0.50 + self.rank * 0.03:
            return rounded(base + abs(normalvariate(0, 1.0)), maxval=5)
        else:
            return rounded(base - abs(normalvariate(0, 0.5)), minval=1)

    def _trait_pool(self) -> dict:
        """Returns the pool of possible traits for this character type."""
        return dict(c.TRAITS, **c.GENDER_TRAITS[self.gender])

    def _roll_traits(self, pool: dict) -> list[str]:
        """Roll for traits from a given pool, returning those that were selected."""
        traits = []
        for trait, chance in pool.items():
            if '/' in trait and isinstance(chance, tuple):
                for subtrait, subchance in zip(trait.split('/'), chance):
                    if random() < subchance:
                        traits.append(subtrait.strip())
                        break
            else:
                if random() < chance:
                    traits.append(trait if '/' not in trait else choice(trait.split('/')).strip())
        return sorted(traits)

    def gen_traits(self) -> list[str]:
        """Returns a list of randomly generated traits for this character.
        Advantages and disadvantages are always listed first.
        """
        advantages = self._roll_traits(c.ADVANTAGES_AND_DISADVANTAGES)
        traits = self._roll_traits(self._trait_pool())
        return advantages + traits

    def gen_tags(self) -> list[str]:
        """
        Not all NPCs are samurai, and not all samurai are from a specific vassal
        House within their great Family, and for many NPCs we don't bother to
        specify what lineage they are from (e.g. when they're from a long way
        off and thus their home lineage politics wouldn't matter).  This returns
        a list of applicable tags for this character.

        For minor clans with only one family or one house, we omit those tags
        since they convey no information (e.g. all Wasp are Tsuruchi).
        """
        # Check if family/house tags would be redundant (only one choice)
        clan_families = config['clan'].get(self.clan, {})
        family_houses = config['family'].get(self.family, {})
        has_multiple_families = len(clan_families) > 1
        has_multiple_houses = len(family_houses) > 1

        return list(
            filter(
                None,
                [
                    self.clan
                    and (self.clan_display + (' Clan' if self.clan != 'imperial' else '')),
                    self.family and has_multiple_families and (self.family_display + ' Family'),
                    self.house and has_multiple_houses and (self.house_display + ' House'),
                    self.lineage and (self.lineage_display + ' Lineage'),
                ],
            )
        )

    def render(self, fname: str) -> str:
        with open(join(c.HERE, 'templates', fname)) as f:
            return re.sub(r'\n{3,}', '\n\n', f.read().format(character=self).strip())

    def to_dict(self):
        return dict(
            self.__dict__,
            **{
                'public': self.render('public_info.txt'),
                'private': self.render('private_info.txt'),
            },
        )

    def __getattr__(self, name):
        if name.endswith('_display'):
            return getattr(self, name.rsplit('_', 1)[0]).replace('_', ' ').title()
        elif name.endswith('_string'):
            return '\n'.join(getattr(self, name.rsplit('_', 1)[0]))
        else:
            raise AttributeError('no such attribute: ' + name)

    def __repr__(self):
        return repr(self.to_dict())


class Samurai(Character):
    def __init__(self, base_rank, clan=None, family=None, house=None, lineage=None, school=None):
        self.base_rank = int(base_rank)
        self.rank = rounded(
            normalvariate(self.base_rank, 0.3), minval=self.base_rank - 1, maxval=self.base_rank + 1
        )
        self.recognition = rounded(normalvariate(self.rank, 1))

        self.clan = clan or weighted_choice(config['clans'])
        self.family = family or weighted_choice(config['clan'].get(self.clan, {}))
        self.house = house or weighted_choice(config['family'].get(self.family, {}))
        self.lineage = lineage or weighted_choice(config['house'].get(self.house, {}))
        self.school = school or weighted_choice(
            config['schools'].get(self.clan, config['schools']['default'])
        )

        Character.__init__(self)

        # Wasp clan Ren lineage samurai are peasantborn
        if self.clan == 'wasp' and self.lineage == 'ren':
            self.traits.append('Peasantborn')
            self.traits.sort()

        # Omit "no [house]" if the house name is the same as the family name
        include_house = self.house and self.house != self.family
        self.full_name = ' '.join(
            filter(
                None,
                [
                    self.family_display,
                    'no {}'.format(self.house_display) if include_house else '',
                    self.personal_name,
                ],
            )
        )

    def _trait_pool(self) -> dict:
        """Samurai get additional samurai-specific traits."""
        return dict(Character._trait_pool(self), **c.SAMURAI_TRAITS)

    def gen_tags(self) -> list[str]:
        return Character.gen_tags(self) + (
            [config['ranks']['Samurai'][str(self.base_rank)]] if self.base_rank > 4 else []
        )


class Peasant(Character):
    def __init__(self, base_rank=0, **ignored):
        self.rank = int(base_rank)
        Character.__init__(self)
        self.recognition = rounded(normalvariate(self.rank + 2, 1))
        self.full_name = self.personal_name
        self.school = ''

    def render(self, fname: str) -> str:
        return re.sub('\nRank: .*', '', super().render(fname))

    def gen_tags(self) -> list[str]:
        return ['peasant']


class Monk(Character):
    def __init__(self, base_rank, **ignored):
        self.rank = int(base_rank)
        Character.__init__(self)
        self.school = ''
        self.full_name = self.personal_name
        self.recognition = rounded(
            normalvariate(10 - self.rank + 1, 2)
        )  # the +1 and higher variance indicates the esteem for monks

    def gen_tags(self) -> list[str]:
        return ['Order of Bishamon', config['ranks']['Monk'][str(self.rank)]]

    def gen_honor(self, base=3.0) -> float:
        variance = 1.1 - self.rank / 10
        direction = choice([-1, 1])
        return rounded(base + direction * abs(normalvariate(0, variance)), minval=1, maxval=5)

    def gen_xp(self) -> int:
        base = 0
        for rank, rank_base in config['rank_xp_bases'][self.__class__.__name__].items():
            if self.rank <= int(rank):
                base = rank_base

        while random() < 0.10:
            base += 50
        return base + 5 * randrange(10)

    def render(self, fname: str) -> str:
        return super().render(fname).replace('\nRank: ', '\nSeat: ')
