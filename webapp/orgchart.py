#!/usr/bin/env python3
"""
Generate a Graphviz org chart for Tsuruchi Kyoma's bounty-hunting hierarchy.

Pulls character data (names, tags, descriptions, avatar URLs) from Obsidian
Portal and renders an org chart showing the chain of command:

    Kyoma (Distinguished Plenipotentiary)
      -> PCs (Haribugyo / Marshals) - also Metsuke for Fox & Sparrow
           -> Escorts reporting to PCs (2 Fox, 2 Sparrow)
      -> Metsuke (Inspectors) - one per domain
           -> Escorts per inspector (not yet generated)

Usage:
    ./env/bin/python3 orgchart.py [--format png|svg|pdf] [--output FILENAME]
"""

import argparse
import os
import re
import urllib.request

import graphviz

from chargen.op import existing_characters, _get_campaign_base_url


AVATAR_DIR = os.path.join(os.path.dirname(__file__), 'avatars')


def download_avatar(url, slug):
    """Download an avatar image and cache it locally. Returns the local path."""
    os.makedirs(AVATAR_DIR, exist_ok=True)
    ext = os.path.splitext(url.split('?')[0])[-1] or '.png'
    local_path = os.path.join(AVATAR_DIR, f'{slug}{ext}')
    if not os.path.exists(local_path):
        urllib.request.urlretrieve(url, local_path)
    return local_path


def build_orgchart(fmt='png', output=None):
    campaign_url = _get_campaign_base_url()
    chars = existing_characters()
    wasp = {c['name']: c for c in chars if any('Wasp' in t for t in c['tags'])}

    # Identify roles
    def find(tag):
        return [c for c in wasp.values() if any(t.lower() == tag.lower() for t in c['tags'])]

    kyoma = wasp.get('Tsuruchi Kyoma')
    inspectors = find('Inspector')
    escorts = find('Escort')
    stewards = find('Household Steward')

    # Imperial magistrates (not Wasp, from the full character list)
    imperial_magistrates = [c for c in chars if any(t == 'Imperial Magistrate' for t in c['tags'])]

    # Sort inspectors by domain name
    inspectors.sort(key=lambda c: c['description'])

    # The PCs' escorts, split by domain
    pc_escorts = [e for e in escorts if 'reporting to the PCs' in e.get('description', '')]
    fox_escorts = [e for e in pc_escorts if any(t == 'Shinden Kitsune' for t in e['tags'])]
    sparrow_escorts = [e for e in pc_escorts if any(t == 'Shiro Suzume' for t in e['tags'])]

    fox_steward = next((s for s in stewards if 'Fox' in s.get('description', '')), None)
    sparrow_steward = next((s for s in stewards if 'Sparrow' in s.get('description', '')), None)

    g = graphviz.Digraph(
        'orgchart',
        format=fmt,
        engine='dot',
    )
    g.attr(
        rankdir='TB',
        bgcolor='#1a1a1a',
        pad='0.5',
        nodesep='0.6',
        ranksep='0.8',
        margin='0.2',
    )
    g.attr(
        'node',
        shape='none',
        fontname='Noto Sans CJK JP',
    )
    g.attr(
        'edge',
        color='#d4a843',
        penwidth='2',
    )

    def char_url(slug):
        return f'{campaign_url}/characters/{slug}'

    def node_html(name, title, avatar_path=None, accent='#d4a843', subtitle=None):
        """Build an HTML-like label for a character node with avatar."""
        img_row = ''
        if avatar_path:
            img_row = (
                f'<TR><TD FIXEDSIZE="TRUE" WIDTH="80" HEIGHT="80">'
                f'<IMG SRC="{avatar_path}" SCALE="TRUE"/>'
                f'</TD></TR>'
            )

        # Shorten display name (drop "Tsuruchi " prefix for compactness)
        display_name = re.sub(r'^Tsuruchi\s+', '', name)

        subtitle_row = ''
        if subtitle:
            subtitle_row = (
                f'<TR><TD><FONT COLOR="#999999" POINT-SIZE="9">{subtitle}</FONT></TD></TR>'
            )

        return (
            f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4"'
            f' BGCOLOR="#2a2a2a">'
            f'{img_row}'
            f'<TR><TD><FONT COLOR="{accent}" POINT-SIZE="14"><B>{display_name}</B></FONT></TD></TR>'
            f'<TR><TD><FONT COLOR="#cccccc" POINT-SIZE="10">{title}</FONT></TD></TR>'
            f'{subtitle_row}'
            f'</TABLE>>'
        )

    def pc_node_html(accent='#d4a843'):
        """Build the PCs group node."""
        return (
            f'<<TABLE BORDER="2" CELLBORDER="0" CELLSPACING="0" CELLPADDING="8"'
            f' BGCOLOR="#2a2a2a" COLOR="{accent}">'
            f'<TR><TD><FONT COLOR="{accent}" POINT-SIZE="16"><B>The PCs</B></FONT></TD></TR>'
            f'<TR><TD><FONT COLOR="#cccccc" POINT-SIZE="11">Haribugyo (Marshals)</FONT></TD></TR>'
            f'</TABLE>>'
        )

    def add_char_node(char, title=None, subtitle=None):
        slug = char['slug']
        avatar_path = None
        if char.get('avatar_url'):
            avatar_path = download_avatar(char['avatar_url'], slug)

        if title is None:
            title = char.get('description', '')

        g.node(
            slug,
            label=node_html(char['name'], title, avatar_path, subtitle=subtitle),
            URL=char_url(slug),
            target='_blank',
        )
        return slug

    # -- Kyoma --
    kyoma_id = add_char_node(kyoma, 'Distinguished Plenipotentiary')

    # -- PCs --
    pc_id = 'pcs'
    g.node(pc_id, label=pc_node_html())
    g.edge(kyoma_id, pc_id)

    # -- Clan clusters --
    # Map each inspector to a clan based on their domain
    clan_map = {
        'Fox': {
            'color': '#5b8c5a',
            'inspectors': [],
            'magistrates': [],
            'escorts': [],
            'steward': None,
        },
        'Sparrow': {
            'color': '#a08050',
            'inspectors': [],
            'magistrates': [],
            'escorts': [],
            'steward': None,
        },
        'Crane': {
            'color': '#6b9bc3',
            'inspectors': [],
            'magistrates': [],
            'escorts': [],
            'steward': None,
        },
        'Scorpion': {
            'color': '#c45555',
            'inspectors': [],
            'magistrates': [],
            'escorts': [],
            'steward': None,
        },
        'Crab': {
            'color': '#7a8a99',
            'inspectors': [],
            'magistrates': [],
            'escorts': [],
            'steward': None,
        },
    }

    domain_to_clan = {
        'Fox': 'Fox',
        'Sparrow': 'Sparrow',
        'Kakita': 'Crane',
        'Etsuko': 'Crane',
        'Daika': 'Scorpion',
        'Reiji': 'Crab',
    }

    for insp in inspectors:
        domain = re.sub(r'^Wasp [Ii]nspector for (the )?', '', insp['description'])
        for key, clan in domain_to_clan.items():
            if key.lower() in domain.lower():
                clan_map[clan]['inspectors'].append(insp)
                break

    # Map Imperial magistrates to clans by domain
    for mag in imperial_magistrates:
        desc = mag.get('description', '')
        for key, clan in domain_to_clan.items():
            if key.lower() in desc.lower():
                clan_map[clan]['magistrates'].append(mag)
                break

    # Assign escorts and stewards to Fox/Sparrow
    clan_map['Fox']['escorts'] = fox_escorts
    clan_map['Fox']['steward'] = fox_steward
    clan_map['Sparrow']['escorts'] = sparrow_escorts
    clan_map['Sparrow']['steward'] = sparrow_steward

    def domain_cluster(
        name,
        label,
        color,
        clan_inspectors,
        clan_magistrates,
        clan_escorts,
        clan_steward,
        parent_id,
        show_domain_subtitle=True,
    ):
        with g.subgraph(name=name) as s:
            s.attr(
                label=f'<<FONT COLOR="{color}" POINT-SIZE="12"><B>{label}</B></FONT>>',
                style='rounded,dashed',
                color=color,
                bgcolor='#222222',
                margin='16',
            )

            # Imperial magistrates
            for mag in clan_magistrates:
                domain = re.sub(r'^Imperial magistrate for (the )?', '', mag.get('description', ''))
                subtitle = domain if show_domain_subtitle else None
                mag_id = add_char_node(mag, 'Imperial Magistrate', subtitle=subtitle)
                s.node(mag_id)

            # Inspectors
            for insp in clan_inspectors:
                domain = re.sub(r'^Wasp [Ii]nspector for (the )?', '', insp['description'])
                subtitle = domain if show_domain_subtitle else None
                insp_id = add_char_node(insp, 'Metsuke (Inspector)', subtitle=subtitle)
                s.node(insp_id)
                g.edge(parent_id, insp_id)

                # Find the matching magistrate for this inspector's domain
                for mag in clan_magistrates:
                    mag_desc = mag.get('description', '').lower()
                    # Match by shared domain keywords
                    for key in domain_to_clan:
                        if key.lower() in domain.lower() and key.lower() in mag_desc:
                            g.edge(
                                mag['slug'],
                                insp['slug'],
                                style='dashed',
                                color='#888888',
                                arrowhead='none',
                                arrowtail='normal',
                                dir='back',
                            )
                            break

                # Placeholder for unassigned escorts
                if not clan_escorts:
                    display_name = re.sub(r'^Tsuruchi\s+', '', insp['name'])
                    placeholder_id = f'{insp["slug"]}_escorts'
                    g.node(
                        placeholder_id,
                        label='<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0"'
                        ' CELLPADDING="4" BGCOLOR="#2a2a2a" COLOR="#666666"'
                        ' STYLE="DASHED">'
                        '<TR><TD><FONT COLOR="#666666" POINT-SIZE="9">'
                        'Gosonin (Escorts)</FONT></TD></TR>'
                        f'<TR><TD><FONT COLOR="#555555" POINT-SIZE="8">'
                        f'(reporting to {display_name})</FONT></TD></TR>'
                        '</TABLE>>',
                    )
                    s.node(placeholder_id)
                    g.edge(insp_id, placeholder_id, style='dashed', color='#666666')

            # Escorts (report to the first/only inspector in this clan)
            if clan_escorts and clan_inspectors:
                insp_id = clan_inspectors[0]['slug']
                for escort in sorted(clan_escorts, key=lambda c: c['name']):
                    escort_id = add_char_node(escort, 'Gosonin (Escort)')
                    s.node(escort_id)
                    g.edge(insp_id, escort_id)

            # Steward (peer to inspectors, one level below magistrates)
            if clan_steward:
                steward_id = add_char_node(clan_steward, 'Household Steward')
                s.node(steward_id)
                g.edge(kyoma_id, steward_id, minlen='3')
                # Invisible edge from a magistrate to force steward down a rank
                if clan_magistrates:
                    g.edge(clan_magistrates[0]['slug'], steward_id, style='invis')

    for clan_name, info in clan_map.items():
        if not info['inspectors']:
            continue
        # Only show domain subtitle when there are multiple inspectors
        # or the domain name differs from the clan name
        show_subtitle = (
            len(info['inspectors']) > 1 or clan_name not in info['inspectors'][0]['description']
        )
        domain_cluster(
            f'cluster_{clan_name.lower()}',
            f'{clan_name} Clan',
            info['color'],
            info['inspectors'],
            info['magistrates'],
            info['escorts'],
            info['steward'],
            pc_id,
            show_domain_subtitle=show_subtitle,
        )

    # Render
    output_name = output or 'orgchart'
    g.render(output_name, cleanup=True)
    print(f'Rendered: {output_name}.{fmt}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Wasp bounty-hunting org chart')
    parser.add_argument(
        '--format',
        '-f',
        default='png',
        choices=['png', 'svg', 'pdf'],
        help='Output format (default: png)',
    )
    parser.add_argument(
        '--output', '-o', default=None, help='Output filename without extension (default: orgchart)'
    )
    args = parser.parse_args()
    build_orgchart(fmt=args.format, output=args.output)
