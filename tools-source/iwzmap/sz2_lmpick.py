"""Pick per-zone lightmap texels from an engine-measured texel gallery (sz2_frames.py gallery.json).

usage: sz2_lmpick.py <gallery.json> <out lm table json> [scale]
Each gallery texel panel is the same white ceramic tile lit only by its texel, so its measured colour is the
texel's rendered light. For every zone the picker chooses the texels whose measured colour is closest (in a
brightness-normalised chroma + luma distance) to the zone's targets: (bright, mid, dark) luma and a tint.
Only uniform panels (low luma std) are used, and texels whose colour changes between neighbours are skipped.
"""
import json, math, sys

gal = json.load(open(sys.argv[1]))['texels']
out = sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

# zone -> tint (r, g, b chroma direction) and target lumas (bright, mid, dark) of a white tile wall
TARGETS = {
    'ticket_hall':    ((0.95, 1.0, 1.10), (0.70, 0.55, 0.30)),
    'stair_a':        ((0.95, 1.0, 1.10), (0.62, 0.48, 0.26)),
    'platform_a':     ((0.92, 1.0, 1.12), (0.66, 0.52, 0.28)),
    'maint_corridor': ((1.25, 0.95, 0.60), (0.58, 0.44, 0.24)),
    'generator_room': ((1.25, 0.95, 0.60), (0.62, 0.48, 0.26)),
    'control_room':   ((1.70, 0.55, 0.45), (0.50, 0.38, 0.20)),
    'service_tunnel': ((1.15, 0.98, 0.78), (0.46, 0.34, 0.18)),
    'platform_b':     ((1.08, 1.02, 0.86), (0.58, 0.44, 0.24)),
    'stair_b':        ((1.05, 1.0, 0.92), (0.58, 0.44, 0.24)),
    'gallery':        ((1.0, 1.0, 1.0), (0.6, 0.5, 0.3)),
}
cands = []
for key, rec in gal.items():
    if rec['std'] > 0.06:
        continue
    r, g, b = [c / 255.0 for c in rec['rgb']]
    s = (r + g + b) / 3 or 1e-6
    cands.append((key, rec['luma'], (r / s, g / s, b / s)))


def dist(c, tint, lum):
    t = sum(tint) / 3
    tn = [v / t for v in tint]
    chroma = math.sqrt(sum((c[2][i] - tn[i]) ** 2 for i in range(3)))
    return abs(c[1] - lum * scale) * 2.0 + chroma


table, report = {}, {}
for zone, (tint, lums) in TARGETS.items():
    table[zone] = {}
    for tone, lum in zip(('bright', 'mid', 'dark'), lums):
        best = min(cands, key=lambda c: dist(c, tint, lum))
        u, v = (float(x) for x in best[0].split(','))
        table[zone][tone] = [u, v]
        report.setdefault(zone, {})[tone] = {'uv': [u, v], 'luma': best[1], 'chroma': [round(x, 2) for x in best[2]], 'target': lum * scale}
json.dump(table, open(out, 'w'), indent=1)
print(json.dumps(report, indent=1))
