# 08 · PACK-A-PUNCH CAMOS

Two camos, one per Pack-a-Punch level. Both come from things that exist in the station (`01-LORE.md`), so a
player who has seen the Signal Cabin and the Converter Hall recognises them on the gun.

- **Level 1: CARRIER** — the signal diagram. The gun becomes a piece of ZERO's track panel.
- **Level 2: MERCURY ARC** — the rectifier bulb. The gun becomes liquid metal with a violet arc living in it.

Reason for the pair: level 1 is graphic, flat and warm (amber on black); level 2 is physical, liquid and cold
(chrome and violet). They cannot be confused at any distance and the step from 1 to 2 reads as "more dangerous".

The owner's reference is the animated Pack-a-Punch camos of recent titles of the series. We take from them the
*ambition* (motion, emissive, a strong idea per tier), not a pattern, palette or texture.

## What the tools allow (checked against `research/A-tools-readiness.md`, section f)

- Works today: a weapon material built from the stock two-UV camo template with our own mask and textures;
  the stock emissive weapon technique; the stock glass technique. Camo is selected by the map's camo index
  (`get_pap_camo`); ported weapons showed the map's camos at the real machine (8 Nov).
- Not stated in the documents: which camo index a custom map gets; any scrolling or pulsing material.
- Missing: new shaders. A look is a stock technique plus our textures.

So each camo is specified in two layers. **Layer S (static, guaranteed)** must already pass review alone.
**Layer M (motion)** is added only through a stock technique that scrolls or pulses, if the camo package finds
one (first task of package K1 in `12-BUILD-PLAN.md`: list every stock technique set used by animated loot camos
and by animated world materials such as screens and signs, and test one on a weapon). No motion is promised to
the owner until that test passes in the game.

---

## LEVEL 1 · CARRIER

**Idea.** A transit signal panel: matte black enamel, thin amber route lines with rounded 45-degree bends,
station ticks, small lamp dots. In motion, lamps travel along the routes like trains on a dispatcher's board.

### Palette (sRGB hex; albedo unless marked emissive)

| Role | Value | Share of surface |
|---|---|---|
| Enamel black (base) | `#0C0D10` | 70 % |
| Enamel wear (edge highlights, in roughness and a slight albedo lift) | `#1B1E24` | 5 % |
| Route line amber (emissive) | `#FFB000`, emissive strength 2.0 | 14 % |
| Lamp white-amber (emissive, the travelling dots and station lamps) | `#FFE7B0`, strength 6.0 | 2 % |
| Signal red (emissive, rare) | `#FF2A1A`, strength 4.0 | under 1 %: at most three lamps per weapon |
| Signal green (emissive, rare) | `#27F58A`, strength 4.0 | under 1 %: at most two lamps per weapon |
| Brass stud (metal, roughness 0.35) | `#B08D4A` | 3 %: small round studs at line junctions |
| Engraved white lettering (tiny, non-emissive) | `#D9D4C4` | 2 %: track numbers "0", "A", "047", chainage marks |

Surface: enamel roughness 0.55 with fine orange-peel normal; route lines are engraved 0.2 mm (normal map) and
filled with light. Metalness 0 except studs.

### Pattern logic

1. Lines are 3 mm wide at weapon scale, run mostly along the barrel axis, and bend only at 45 or 90 degrees
   with a 4 mm radius. Two or three parallel routes, spaced 9 mm, that merge and split at junctions. (Thin,
   many lines read as a circuit board in first person; few, bold lines read as a diagram.)
2. Every junction has a brass stud. Every 40 mm a short perpendicular tick (a station).
3. One route on each weapon ends in a filled amber disc with a black centre: the Zero roundel. It sits near the
   rear sight or the receiver's widest flat. It is the only large shape.
4. Lines never cross moving parts' seams at an angle: at a seam they stop in a small rounded terminal.
5. The mask tiles along the barrel axis every 180 mm, mirrored on the off side so left and right are not twins.

### Motion (layer M)

- Lamp dots travel along routes at 60 mm per second, one dot per route, spaced so that no two arrive at a
  junction together. Built as a second emissive mask scrolling along the U axis of UV2 (routes are laid straight
  in UV2 for this purpose even where they bend on the model).
- Every 2.4 seconds one signal lamp changes aspect (red to green or back): a slow two-frame flip, not a blink.
- Reactive (only if a material parameter can be driven from script; otherwise dropped): on firing, all route
  lines flash to lamp white for 80 ms.

### It must NOT look like

A circuit board (no pads, no chips, no right-angle maze), neon "light-cycle" lines on a grid, hexagons, a city
metro map with coloured lines (only amber, with rare red and green lamps), carbon fibre, or flames. No blue.

### Small pistol and large LMG

- Pistol: two routes only, the roundel on the slide's rear third, one red lamp. The slide's flat is the canvas;
  the grip stays plain enamel.
- LMG: three routes on the receiver, two continuing down the barrel shroud; the feed cover carries a junction
  fan (three lines merging to one). Belt box: plain enamel with a single engraved "047".
- Rule for both: at least 60 % plain enamel on every part. The camo is drawn *on* the gun, it does not wrap it.

### Three reference directions (written, for the image tool and the material builder)

1. "Top-down macro photograph of a 1970s railway signalling control panel: matte black enamelled steel plate,
   engraved track diagram lines filled with warm amber back-light, small round indicator lamps, brass screw
   heads, fine dust in the engraving, no hands, no text larger than 2 mm, flat even studio light."
2. "A vintage audio mixing desk fader panel repainted as a track diagram: black wrinkle paint, amber silk-screen
   lines with rounded 45-degree bends, three tiny jewel lamps (two red, one green), worn edges showing dark steel."
3. "Tileable mask, pure black background, white vector lines 1.5 px wide with rounded 45-degree bends, lines
   mostly horizontal, merging and splitting at dots, perpendicular tick marks at regular intervals, one filled
   ring; orthographic, no perspective, no glow, no gradient." (this one produces the mask itself)

---

## LEVEL 2 · MERCURY ARC

**Idea.** The inside of a mercury-arc rectifier: a pool of liquid mercury under glass with a violet arc dancing
on it. The weapon looks poured, heavy and alive; the arc crawls over it and gathers in the recesses.

### Palette

| Role | Value | Share |
|---|---|---|
| Mercury skin (metal 1.0, roughness 0.24: a soft mirror, not a hard one) | albedo `#C9CED6`, with a faint baked environment in it (blurred amber and white station lamps) so that it reads as lit metal even where the map's reflection probes hold only darkness | 62 % |
| Mercury shadow tint (in occluded folds, via albedo) | `#3A3F4A` | 12 % |
| Arc core (emissive) | `#E9E0FF`, strength 8.0 | 2 % |
| Arc body (emissive) | `#8A5CFF`, strength 4.0 | 9 % |
| Deep ultraviolet glow in recesses (emissive, soft) | `#2A0A5E`, strength 1.5 | 10 % |
| Teal fringe (emissive, hair-thin, at arc edges only) | `#35E0D0`, strength 2.0 | 1 % |
| Blackened glass (on optics and magazines only, glass technique) | `#0A0612`, 85 % opaque | 4 % |

Surface: the normal map is a slow, large liquid ripple (wavelength 25 to 40 mm), no fine noise; the metal must
read as one continuous skin with beads of mercury gathering along lower edges (small hemispherical normals, 1 to
3 mm, sparse).

### Pattern logic

1. No drawn pattern. The form is the pattern: reflections of the map on a liquid skin.
2. The arc is a branching filament mask, three to six branches, thicker at one root. Roots sit in recesses
   (ejection port, rail slots, flutes); branches reach along edges, never across wide flats.
3. Ultraviolet glow fills every recess deeper than about 2 mm (baked from the weapon's ambient occlusion,
   inverted, then tinted).
4. Mercury beads only on downward-facing edges, at most twelve per weapon.

### Motion (layer M)

- Two arc masks scroll against each other (speeds 0.11 and 0.07 UV per second, different directions) and are
  multiplied: where they overlap the arc is visible. This produces a filament that crawls and re-forms without
  ever repeating visibly inside 20 seconds.
- The ripple normal scrolls at 0.02 UV per second (barely perceptible; the reflection breathes).
- The arc root flickers in brightness between 70 % and 100 % at an irregular 9 to 14 Hz (a baked flicker strip).
- Reactive (same condition as level 1): on firing, the arc brightness doubles for 120 ms and decays over 400 ms.

### It must NOT look like

Chrome car paint with rainbow reflections, "dark matter" galaxies or star fields, purple lightning bolts drawn
as zigzags, plasma balls, oil-slick iridescence, molten gold, or cracks with lava. No amber (that is level 1's
colour), no pure blue, no pink.

### Small pistol and large LMG

- Pistol: the slide is the mercury; one arc root in the ejection port with two short branches; frame slightly
  darker (shadow tint) so the gun is not a featureless mirror in the hand.
- LMG: arc roots in three places (port, feed tray, barrel shroud vents); the long barrel carries the ripple so
  the length does not read as a flat tube; belt box in blackened glass with the glow inside.
- Rule for both: the arc covers no more than 12 % of visible surface at any moment; if it reads as "purple gun",
  it failed.

### Three reference directions

1. "Macro photograph of a working mercury-arc rectifier valve from a 1930s traction substation: thick glass
   bulb, pool of liquid mercury at the bottom, a violet-white arc spot skating on the mercury surface, soft
   ultraviolet haze inside the glass, dark industrial background, no people."
2. "A handgun-sized block of liquid mercury held in shape, perfectly smooth, studio light with one soft box,
   small beads of mercury hanging from the lower edge, dark grey background; no engraving, no pattern."
3. "Tileable mask, pure black background, thin white branching electrical filament like a Lichtenberg figure
   drawn with a single hair, three to six branches, thicker root on the left, no glow, no zigzag, organic."

---

## Building notes (for package K1)

- UV2 carries the camo (the two-UV camo template is proven on the ported weapons). The masks above are authored
  in UV2 space; stock IWZ weapons already have their camo UVs.
- Textures per camo: albedo, normal, packed roughness/metal/occlusion, emissive, and for layer M one or two
  scrolling masks. Target 1024 x 1024 each (512 if the mod size budget requires).
- Images come from procedural generators first (lines, filaments, ripples are all procedural); the image tool
  is allowed only for the grime and wear overlays, with the reference texts above, and every result is judged.
- Two things must be found before any art is built. (1) Which camo index a custom map receives (read
  `get_pap_camo` in the dump and the camo table; the readiness digest marks it "not stated"). (2) Where two
  **new** camo rows can live: K1's first probe is a new camo-table row shipped in the map's zone, picked on
  this map and seen on a stock weapon. Fallbacks, in order: re-texture two existing camo indexes inside the
  map's zone only; or carry the camos on the weapons' own upgraded definitions (a look change by definition
  swap is the proven route for the ported weapons), starting with the four wonder weapons.

## Judging criteria (independent reviewers, on frames from the game, never on texture sheets)

Each scored 0 to 10; a camo ships at an average of 8 with no single score under 7.

1. **Idea reads in one second**: a reviewer who has not read this page names "signal panel / track diagram"
   for level 1 and "liquid metal with electric arc" for level 2.
2. **Belongs to the map**: recognisable relation to the Signal Cabin panel and the rectifiers in frames of
   those rooms placed side by side.
3. **Tier step**: ten of ten reviewers rank level 2 as the higher tier without being told.
4. **Small and large**: passes on the smallest pistol and the largest LMG, first person and world model at 5 m.
5. **Restraint**: the plain-surface rules are met (60 % enamel; arc under 12 %).
6. **Not generic**: none of the "must not look like" items is named by any reviewer.
7. **Motion** (only when layer M ships): no visible loop within 10 seconds of footage, no strobing, and the
   static frame still passes criteria 1 to 6.
8. **Darkness**: judged in the Boneyard and the unlit Sump first (the darkest zones), then in the Terminus
   (the brightest). Level 2 must read as metal, not as a black slab, in the Boneyard.
9. **Cost**: frame time with four upgraded weapons on screen within noise of the stock camo (performance
   recorder, three runs a side).
