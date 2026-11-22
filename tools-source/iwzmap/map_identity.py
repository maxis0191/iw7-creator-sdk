"""The name of a generated zombies map: what the game needs of it, the arena file, the title.

usage: map_identity.py resolve <emit folder> [--map NAME]            print the map name to build (layout.json "map" unless --map)
       map_identity.py check NAME                                     exit 0 / 1: may this name be a usermap
       map_identity.py arena NAME TITLE OUT [--description TEXT]      write NAME.arena (the stock arena text format)
       map_identity.py title NAME                                     the title a map gets when none is given
       map_identity.py strings NAME TITLE BASE.json OUT.json          BASE's strings plus IWZ_MAPNAME_<NAME> = TITLE (the map's own localized title for scripts)

Limits come from the client (iw7-mod src/client/component/arena.cpp, read 23 Nov 2026):
  * a loadname starting with cp_ is what makes a usermap a Zombies map (MAP_INFO_ALIENS);
  * map_info fields are fixed: loadname 16 bytes (name at most 15 characters), longname and description 32 bytes
    (usermaps turn them into literals with a 0x1F prefix: at most 30 characters), mapimage and mapvoteimage 32 bytes
    (image_<name>_vote at most 31: no limit beyond the 15 of the name);
  * usermap_exists(name) is the file usermaps/<name>/<name>.ff; the arena is usermaps/<name>/<name>.arena;
  * the 64-entry arena budget is shared with the stock maps.
The regular expression of the local runner (ops/iwzmap/Test-IWZMapLocal.ps1) is ^cp_[a-z0-9_]+$.
"""
import json
import os
import re
import sys

NAME_RE = re.compile(r'^cp_[a-z0-9_]+$')
MAX_NAME = 15
MAX_TITLE = 30
# stock zombies and front end zones: a usermap of the same name would shadow or be shadowed by the stock zone
RESERVED = {'cp_zmb', 'cp_rave', 'cp_disco', 'cp_town', 'cp_final', 'cp_frontend', 'cp_sneak', 'cp_alien'}


def check_name(name):
    """Raises ValueError with the reason when the name cannot be a generated zombies usermap."""
    if not NAME_RE.match(name or ''):
        raise ValueError('map name %r: lower case letters, digits and _ only, starting with cp_ (the prefix is what makes it a Zombies map)' % name)
    if len(name) > MAX_NAME:
        raise ValueError('map name %r is %d characters: the engine\'s loadname field holds %d' % (name, len(name), MAX_NAME))
    if name in RESERVED:
        raise ValueError('map name %r is a stock map name' % name)
    if name.endswith(('_art', '_load', '_base')):
        raise ValueError('map name %r ends in a zone suffix the loader gives a meaning (_art, _load, _base)' % name)
    return name


def default_title(name):
    body = name[3:] if name.startswith('cp_') else name
    return body.replace('_', ' ').strip().upper() or name.upper()


def check_title(title):
    if not title or len(title) > MAX_TITLE:
        raise ValueError('title %r: 1 to %d characters' % (title, MAX_TITLE))
    if '"' in title or any(ord(c) < 32 or ord(c) > 126 for c in title):
        raise ValueError('title %r: printable ASCII without double quotes' % title)
    return title


def arena_text(name, title, description='An IWZ custom map'):
    """The stock arena text format (CRLF, tabs), as the arena of Station Zero RC1. Image names follow arena.cpp."""
    check_name(name)
    check_title(title)
    check_title(description)
    rows = [
        '{',
        '\tmap\t\t\t"%s"' % name,
        '\tlongname\t"%s"' % title,
        '\tgametype\t"zombie Aliens escape"',
        '\tdefaultgametype "zombie"',
        '\tdescription "%s"' % description,
        '\tmapimage    "image_%s"' % name,
        '\tmapvoteimage "image_%s_vote"' % name,
        '\tmappack\t\t"0"',
        '}',
    ]
    return '\r\n'.join(rows) + '\r\n'


def strings(name, title, base):
    '''The {KEY: text} json of the map's own strings: the base file's (the perk strings) plus the title under IWZ_MAPNAME_<NAME>.'''
    check_name(name)
    check_title(title)
    out = json.load(open(base, encoding='utf-8')) if base and os.path.isfile(base) else {}
    out['IWZ_MAPNAME_' + name.upper()] = title
    return out


def layout_map(src):
    p = os.path.join(src, 'layout.json')
    if not os.path.isfile(p):
        return ''
    return str(json.load(open(p, encoding='utf-8')).get('map') or '')


def resolve(src, requested=''):
    """The map name of a build: the requested one, else the exporter's (layout.json "map"), else cp_iwz.

    The emit carries the name in its level script calls and its modules (modules/<map>_<name>.gsc, the Capsule Post call), so a
    request that differs from layout.json is refused when the emit has modules; without them only the level script paths of
    the cp_iwz template move (assemble.py does that), which is safe."""
    lay = layout_map(src)
    name = requested or lay or 'cp_iwz'
    if requested and lay and requested != lay:
        mods = os.path.join(src, 'modules')
        if os.path.isdir(mods) and any(f.endswith('.gsc') for f in os.listdir(mods)):
            raise ValueError('-Map %s but the emit was exported as %s and carries modules named after it: export it again with the '
                             'scene\'s iwz_map set to %s' % (requested, lay, requested))
        if lay != 'cp_iwz':
            raise ValueError('-Map %s but the emit was exported as %s: only an emit named cp_iwz can be renamed at build time' % (requested, lay))
    return check_name(name)


def main(argv):
    if not argv:
        sys.stderr.write(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == 'resolve':
            req = ''
            if '--map' in rest:
                i = rest.index('--map')
                req = rest[i + 1]
                rest = rest[:i] + rest[i + 2:]
            print(resolve(rest[0], req))
        elif cmd == 'check':
            check_name(rest[0])
        elif cmd == 'title':
            print(default_title(rest[0]))
        elif cmd == 'strings':
            name, title, base, out = rest[:4]
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(strings(name, title, base), f, indent=2)
        elif cmd == 'arena':
            desc = 'An IWZ custom map'
            if '--description' in rest:
                i = rest.index('--description')
                desc = rest[i + 1]
                rest = rest[:i] + rest[i + 2:]
            name, title, out = rest[:3]
            text = arena_text(name, title, desc)
            with open(out, 'w', newline='') as f:
                f.write(text)
        else:
            sys.stderr.write('map_identity: unknown command %r\n' % cmd)
            return 2
    except ValueError as e:
        sys.stderr.write('map_identity: %s\n' % e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
