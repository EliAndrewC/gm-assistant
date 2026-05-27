"""
Ministry generation utilities for creating complete ministry rosters.

This module provides functions to generate ministers with appropriate
ranks, tags, and descriptions for each of the six ministries of Rokugan.
"""

from chargen.character import Samurai
from chargen import constants as c


def generate_minister(ministry_name, rank, clan=None, family=None, house=None):
    """
    Generate a minister character with ministry-specific attributes.

    Args:
        ministry_name: One of the six ministries from c.MINISTRIES
        rank: Base rank (6=Deputy Provincial, 7=Provincial, 9=Deputy, 10=Minister)
        clan: Optional clan selection
        family: Optional family selection
        house: Optional house selection

    Returns:
        dict: Character data with ministry-specific tags and description
    """
    # Generate base samurai character
    character = Samurai(base_rank=rank, clan=clan, family=family, house=house)

    # Get rank display name from config
    rank_names = {
        6: 'Deputy Provincial Minister',
        7: 'Provincial Minister',
        9: 'Deputy Minister',
        10: 'Minister',
    }
    rank_display = rank_names.get(rank, 'Minister')

    # Convert to dict
    char_dict = character.to_dict()

    # Add ministry-specific tag (rank tag is already added by Samurai.gen_tags())
    ministry_tag = ministry_name
    char_dict['tags'].append(ministry_tag)

    # Add summary suggestion (user should edit this)
    ministry_title = ministry_name.replace('Ministry of ', '')
    char_dict['summary'] = f'{rank_display} of {ministry_title}'

    # Store ministry metadata
    char_dict['ministry'] = ministry_name
    char_dict['ministry_rank'] = rank_display

    return char_dict


def generate_ministry_roster(rank, clan=None, family=None, house=None):
    """
    Generate a complete roster of 6 ministers, one for each ministry.

    Args:
        rank: Base rank for all ministers
        clan: Optional clan for all ministers
        family: Optional family for all ministers
        house: Optional house for all ministers

    Returns:
        list: List of 6 character dicts, one per ministry
    """
    roster = []
    for ministry in c.MINISTRIES:
        minister = generate_minister(ministry, rank, clan, family, house)
        roster.append(minister)
    return roster
