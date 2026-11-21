"""Check a map voice script (iwz.voice-script/1) before any line is generated, in under a second.

usage: voice_script_check.py <script.json> [--lang en,fr] [--wps 2.6] [--json report.json]

Fails (exit 1) when: an id is not unique; a line names a speaker or a hook the script does not define; a language text
is missing or empty; a bracket tag is not in its speaker's tags_allowed (the Voice of the Rapid has none: she is a
recording); a hook status is not one of exists / event / stock / to_wire / future; a line with max_s is longer than that at
--wps words per second; a voice_id is filled with something that is not a string (ids come from a voice listing, never
from memory). Prints per language and speaker the line count and the characters (what text-to-speech is billed on),
the lines that play today (hook status exists and no unproven routing: the first batch to generate) and the lines
whose event exists but needs a play call.
"""
import argparse, json, re, sys
from collections import defaultdict

STATUS = ('exists', 'event', 'stock', 'to_wire', 'future')
TAG = re.compile(r'\[([a-z][a-z ]*)\]')        # [whispering]; [0.8 s] and [0,8 s] (timed silences) do not match


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script'); ap.add_argument('--lang', default='en,fr'); ap.add_argument('--wps', type=float, default=2.6)
    ap.add_argument('--json')
    a = ap.parse_args()
    doc = json.load(open(a.script, encoding='utf-8'))
    langs = a.lang.split(',')
    spk, hooks, lines = doc.get('speakers', {}), doc.get('hooks', {}), doc.get('lines', [])
    fails, seen = [], set()
    chars = defaultdict(int); count = defaultdict(int)
    for h, d in hooks.items():
        if d.get('status') not in STATUS:
            fails.append('hook %s: status %r' % (h, d.get('status')))
    for s, d in spk.items():
        if d.get('voice_id') is not None and not isinstance(d['voice_id'], str):
            fails.append('speaker %s: voice_id must be null or a listed id string' % s)
    for ln in lines:
        i = ln.get('id')
        if i in seen:
            fails.append('duplicate id %s' % i)
        seen.add(i)
        if ln.get('speaker') not in spk:
            fails.append('%s: unknown speaker %r' % (i, ln.get('speaker')))
            continue
        if ln.get('hook') not in hooks:
            fails.append('%s: unknown hook %r' % (i, ln.get('hook')))
        allowed = set(spk[ln['speaker']].get('tags_allowed', []))
        for lg in langs:
            t = (ln.get(lg) or '').strip()
            if not t:
                fails.append('%s: no %s text' % (i, lg)); continue
            for tg in TAG.findall(t):
                if '[%s]' % tg not in allowed:
                    fails.append('%s (%s): tag [%s] not allowed for %s' % (i, lg, tg, ln['speaker']))
            words = len(TAG.sub('', t).split())
            if ln.get('max_s') and words / a.wps > ln['max_s']:
                fails.append('%s (%s): %d words, %.1f s at %.1f words/s, over max_s %s' % (i, lg, words, words / a.wps, a.wps, ln['max_s']))
            chars[(lg, ln['speaker'])] += len(t); count[(lg, ln['speaker'])] += 1
    st = lambda ln: hooks.get(ln.get('hook'), {}).get('status')
    first = [ln['id'] for ln in lines if st(ln) == 'exists' and not ln.get('routing')]
    wire = [ln['id'] for ln in lines if st(ln) == 'event' and not ln.get('routing')]
    by_status = defaultdict(int)
    for ln in lines:
        by_status[hooks.get(ln.get('hook'), {}).get('status', '?')] += 1
    print('%d lines, %d speakers, %d hooks; triggers: %s' % (len(lines), len(spk), len(hooks), dict(by_status)))
    for lg in langs:
        tot = sum(v for (l_, _), v in chars.items() if l_ == lg)
        print('  %s: %d characters (%s)' % (lg, tot, ', '.join('%s %d/%d' % (s_, count[(lg, s_)], chars[(lg, s_)]) for (l_, s_) in sorted(chars) if l_ == lg)))
    print('  plays today: %d lines (%s)' % (len(first), ' '.join(first)))
    print('  event exists, needs a play call: %d lines (%s)' % (len(wire), ' '.join(wire)))
    for f in fails:
        print('FAIL', f)
    print('voice script: %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails)))
    if a.json:
        json.dump({'schema': 'iwz.voice-script-check/1', 'fails': fails, 'first_batch': first, 'needs_play_call': wire,
                   'chars': {'%s/%s' % k: v for k, v in chars.items()}}, open(a.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
