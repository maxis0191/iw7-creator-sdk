# 10 · EMOTES

Sixty-five emotes for STATION ZERO: 40 dances (21 originals animated by us from the map, 19 library clips), 25 calm gestures, and a radial wheel in the Maxis design
system to pick them. Facts about the tools come from `research/A-tools-readiness.md` (section n, packages C1, C2,
U1) and `research/B-maxis-ui.md` (tokens, the two delivery routes, limits). Where a detail was not fixed by the
owner it is marked "(decided here)". Where a fact is not in the research it is marked "unproven" or "not stated".

## 0. Status, said plainly

This chapter is design only. **No emote can ship, and none can be shown to anyone, until four things are proven.**

| Gate | What must be true | State today (source) |
|---|---|---|
| G1 | A path from Blender or glTF to a game animation (package C1) | running, not landed (A, CC) |
| G2 | One animation of ours plays in the game and is measured bone by bone against its source (package C2) | open, needs C1 (A) |
| G3 | A full-body animation plays on a real player's world model and a second client sees it | unproven ("Third person on real players unproven", CC Models row) |
| G4 | The emoting player sees a third-person view of it | unproven; the client ignores a server `setclientdvar cg_fov` (BWW), so a client dvar is not a known route |

The two picker tiers (section 5) also have their own first proofs: Tier 2 needs a movement-only freeze (section 5.2),
Tier 1 needs key capture, cursor position and gamepad events in Lua (section 5.1). None of them is a gate for the
others, but without G1 to G4 the picker has nothing to pick.

If G3 fails, the only animation route proven in the game is first-person hand animation (BO3 weapon animations
retargeted onto the game's hands, CC). Then the calm gestures that read in first person (Wave, Thumbs Up, Point,
Fist Pump, Blow a Kiss, Check Watch, Coffee Sip) could exist for their owner only, and no dance could. That is the
fallback, and it is a loss, not a substitute.

## 1. Sources, licences, originality

- **Allowed sources:** Mixamo (free to use in games with an Adobe account), the CMU motion capture database (free for
  any use), and "to animate" (A: keyframed by us in Blender). Real-world social dance steps are allowed. Long
  recognisable choreographies tied to one song are not. No music is attached to any emote.
- **Nothing from another publisher's game:** no emote name, clip, music or look. Every name in section 2 is ours.
  The Mixamo search terms appear only in the Source column; they are the catalogue's words, not names players see.
- **Mixamo:** re-read the current terms at download time and record the date and the terms version in the ledger.
  The raw FBX files are not committed to any repository (only the baked clip inside a zone ships), the manifest
  `ops/emotes/emotes.json` records term, download date and clip id. (decided here)
- **CMU:** free for any use; the credits chapter carries one thank-you line. Files are BVH or AMC/ASF with a known
  skeleton, retargeted in Blender through the same path as Mixamo.
- **To animate (A):** built from a beat sheet at 120 bpm (one beat = 0.5 s), as a counting aid only. A beat sheet is
  the written motion in section 2; it is the brief for the animator.
- **Motion text for M and CMU rows** states what the catalogue term names. It is checked against the real clip at
  download and corrected here, so a row never claims more than the clip does. (decided here)
- **Retargeting:** every clip goes through the C1 path onto the game's player skeleton. Whether the four hero bodies
  share one skeleton is not stated in the research. If they do not, each clip is retargeted once per skeleton and
  the size estimate in section 7 doubles.

## 2. The 65 emotes

Conventions for every row:

- **ID** = the number the server and the wheel use (1 to 40 dances, 41 to 65 calm). Calm IDs follow the owner's list order.
- **Page** = `D1` to `D6` (DANCE pages: STATION 1 to 3, SOCIAL 1 and 2, FLOOR), `C1` to `C3` (CALM pages), then `.n` = wedge 1 to 8, wedge 1 at 12 o'clock,
  clockwise. Wave (41) is the centre button of every page. Section 4.2 lists the pages whole.
- **L/S** = loop or one-shot. **Sec** = the loop body for a loop (it repeats seamlessly), the whole clip for a one-shot.
- Every emote stays inside a 60-unit radius of where the player stood and ends with net root travel of zero. Rows say
  when the real excursion is above 40.
- Seven emotes change the body's base posture (floor work, sitting, leaning, phone, newspaper). They also have an
  **in** clip (1.0 s) and an **out** clip (0.8 s), marked "+in/out". Standing dances have no separate in or out: the
  player blends from the idle pose (blend length is a C2 result, not assumed).
- A = to animate. M "term" = Mixamo catalogue search term, **verify at download**. CMU = subject area, verify trial.

### 2.1 Dances, 1 to 40

Rows 1 to 21 are the 21 **originals**, animated by us (source A): the 12 station dances and the nine that come from the
map itself (13 to 21). Rows 22 to 40 are the 19 **library clips** (source M or CMU), named plainly: a library
clip's name says what the dance is.

| ID | Name | Page | Motion (feet, hips, arms, head; beats at 120 bpm) | L/S | Sec | Source | Note |
|---|---|---|---|---|---|---|---|
| 1 | Turnstile Hop | D1.1 | Right hand on an imaginary hip-high bar. Beats 1-2: crouch 10 cm, both hands push down on the bar. Beats 3-4: hop sideways over the bar to the left (30 units across, 14 units high), legs tucked. Beat 5: land on both feet, knees bent. Beats 6-7: 180 degree pivot on the left ball of the foot, head leads. Beat 8: hands settle on the bar. Beats 9-16: the same hop mirrored back to the start. | L | 8.0 | A | The map's own joke (01-LORE, turnstiles). Excursion 30, ends where it began. |
| 2 | Watch the Edge | D1.2 | Beats 1-2: slow exaggerated step to the right, knee to hip height, stride 36 units, torso leaning back, head turned down. Beat 3: feet together, hands on the lapels. Beats 4-5: right index finger jabs at the floor, head nods on 4 and 5. Beats 6-8: the same giant step back over the edge. Beats 9-12: shoulder shimmy (shoulders alternate 5 cm every half beat), finger wagging at the edge. | L | 6.0 | A | The station announcement as a dance. Excursion 36. |
| 3 | Third Rail Shimmy | D1.3 | Beats 1-2: right toe taps forward and hesitates. Beat 3: contact; a 12 Hz jitter of plus or minus 3 cm starts in the foot and climbs ankle, knee, hip, ribs, shoulders over 1.5 beats. Beat 5: head snaps back 15 degrees, fingers splay, arms out and shaking. Beats 6-8: full-body jitter held. Beat 9: contact breaks, body goes limp (shoulders drop 8 cm, knees sag). Beats 10-12: shake out each wrist and one leg, step back to the start. | L | 6.0 | A | Amplitude kept at 3 cm so it reads at distance. Excursion 20. |
| 4 | Rink Glide | D1.4 | Beats 1-4: two long glides: weight on the left foot, right foot slides out 25 units to the side and back over 2 beats, then swap; knees soft, torso 10 degrees forward, hands alternately behind the back. Beats 5-8: forward arm rolls, one circle per beat, hips swaying. Beats 9-12: glides again, one arm trailing high. Beats 13-16: toe-stop spin: 360 degrees on the left toe, right leg trailing, arms out, final pose on beat 16 with knees bent. | L | 8.0 | A | Same joke as the Rollers on skates (07-ENEMIES). Default favourite. Excursion 25. |
| 5 | Conga Car | D1.5 | A 4-beat cycle played twice: step, step, step, kick, alternating the kicking leg (kick to knee height on beat 4). Hips swing 8 cm sideways on every step. Leader clip: hands on hips, head bobs on beats 1 and 3. Follower clip: both arms forward and slightly raised, hands resting on the shoulders of the player in front (set for a 36 unit spacing). | L | 4.0 | A (2 clips) | JOINABLE, up to 8 (section 3.4). The only emote with a second clip by design. |
| 6 | Late Shift Shuffle | D1.6 | Arms straight out at chest height, elbows locked, hands limp. A heavy stomp on every beat, alternating feet (knee to 60 degrees, foot dropped early so the heel lands on the beat). Head tilts 20 degrees right on beat 2 and left on beat 6. Shoulder drops of 6 cm on beats 3 and 7. Torso leans 8 degrees forward. | L | 4.0 | A | Parody of the enemy (01-LORE, section 8); silent. Stays in place. |
| 7 | Ticket Punch | D1.7 | Left hand holds an imaginary ticket at chest height. Right hand clamps an imaginary punch on every beat (thumb and fingers close, hand dips 8 cm). Hips pop 6 cm to the side opposite the clamping hand on every beat. Beats 4 and 8: the ticket is flicked over the shoulder and the head follows it. Knees bend on the off-beat. | L | 4.0 | A | The conductors of the 23:47 carry a punch (01-LORE, M2). |
| 8 | Signal Arms | D1.8 | Three arm positions of a railway semaphore: 45 degrees up (clear), horizontal (caution), 45 degrees down (stop). Twelve snaps, one per beat, through the pairs (both horizontal, right up and left down, both up, right down and left horizontal, both down, left up and right horizontal, and back); each snap lasts 3 frames (0.1 s), then holds. Torso stays vertical, head snaps toward the higher arm, knees bounce 6 cm on the off-beat. | L | 6.0 | A | Robot-clean silhouette that reads from far away; fits the Signal Engineer. |
| 9 | Step Class '84 | D2.1 | Beats 1-4: four step-touches side to side, arms pulling in at the chest each time. Beats 5-8: grapevine to the right (step, cross behind, step, touch) with a clap on 8. Beats 9-12: four alternating knee lifts to hip height with the opposite elbow pulled back. Beats 13-16: arms sweep overhead into a V on 13 and come down by 16, ending with a wipe of the forehead. | L | 8.0 | A | Aerobics class, the year the film is set. Excursion 45 (grapevine). |
| 10 | The Sprinkler | D2.2 | Left hand behind the head, elbow out. Right arm straight forward at shoulder height. Beats 1-4: the right arm moves in five short jerks (0.1 s snap, then stop) from the front to 90 degrees right, head bobbing on each jerk, then snaps back to the front. Beats 5-8: swap hands and repeat to the left. Knees bounce every beat. | L | 4.0 | A | Real-world social step. |
| 11 | The Lawnmower | D2.3 | Beats 1-2: knees bent, right fist yanks an imaginary starter cord twice (arm up and back, elbow at ear height), left hand on hip. Beats 3-8: both hands grip an imaginary handle at waist height and push forward and pull back 20 cm each beat; feet shuffle 10 units; torso leans 12 degrees; head scans left on beat 5 and right on beat 7. Beat 8: stop and wipe the brow. | L | 4.0 | A | Real-world social step. |
| 12 | Pendulum | D2.4 | Feet planted shoulder width, knees bent. Hips swing to one side while straight arms swing the other way as a counterweight. Beats 1-4: one swing per 2 beats, amplitude 20 degrees. Beats 5-8: one swing per beat, 25 degrees. Beats 9-12: one swing per half beat, 30 degrees, then a hard stop on 12 back at the start pose. Head stays level. | L | 6.0 | A | Accelerating clock gag; the station clocks are stopped, this one is not. |
| 13 | Flap Board | D2.5 | Torso and arms turn in sharp quarter turns, one per beat, like split-flap digits. Beats 1-4: forearms hinge from vertical to horizontal in four hard quarter turns (each over 3 frames, then hold), head snapping to match. Beats 5-8: the same through shoulders and chest, 90 degrees a beat, feet pivoting on the balls. Beats 9-12: a cascade, left arm, torso, right arm flipping a half beat apart, ending with both hands flat and a 2 cm settle. | L | 6.0 | A | The Fare Hall board (01-LORE, section 9). Excursion 5. |
| 14 | Yellow Line | D2.6 | Toes on an imaginary platform edge, a teetering balance walk heel to toe along a 40 unit line and back, arms windmilling in opposite circles to hold balance. Beats 4 and 10: a foot overshoots and snaps back. Head down at the edge. Beats 11-12: arms settle, a relieved wipe of the brow. | L | 6.0 | A | Every platform has the line. Excursion 40, ends where it began. |
| 15 | Dead Escalator | D2.7 | Beats 1-8: the descending-stairs mime, one hand on an imaginary rail, steps down in place, the body lowering 6 cm every two beats on a knee bend, a lurch on beat 7 when the steps turn out not to move. Beats 9-16: the climb back up the same stairs, torso leaning into it, shoulders heaving, a shrug of defeat on beat 16, then a reset. | L | 8.0 | A | The Escalator Hall (02-WORLD, zone 3). In place. |
| 16 | Token Flip Strut | D2.8 | Beats 1-2: the right thumb flips an imaginary token overhead (the hand rises 25 cm, the eyes follow it). Beat 3: the token is caught behind the back with the left hand. Beats 4-7: a four-step strut, chest out, chin up, hips rolling, 25 units forward on beats 4-5 and back on 6-7, arms swinging in opposition. Beat 8: the token is flipped again and the loop restarts. | L | 4.0 | A | The Rapid's tokens (wiki/tokens.md). Excursion 25. |
| 17 | Rush Hour Squeeze | D3.1 | Right hand holds an imaginary overhead strap, left hand clutches a bag at the chest. Beats 1-4: the body sways 12 cm with the imaginary carriage, knees soft, feet planted. Beats 5-8: squeezed from both sides, shoulders rise to the ears, elbows pinned, head tilting between two invisible neighbours, a 6 cm shove on every beat. Beats 9-12: the carriage lurches, the whole body tilts 15 degrees and corrects, then a sigh. | L | 6.0 | A | The commuters of 01-LORE. In place. |
| 18 | Doors Closing | D3.2 | Forearms vertical at the sides, then chopped together at chest height like door leaves on a two-note bounce: close on the beat, bounce back open to 30 cm on the half beat, close again. Beat 3: a step back. Beat 4: a chop. The second half mirrors it with a step forward. The head turns toward the closing doors on every chop. | L | 4.0 | A | The Conductor pulls the car doors shut (07-ENEMIES, section 1). Excursion 20. |
| 19 | Capsule Pop | D3.3 | Beats 1-3: crouch small, arms folded in, a fast 2 cm tremble. Beat 4: spring up star-shaped, arms and legs wide, a 25 cm jump. Beat 5: land in a stagger, one foot sliding 15 units, arms windmilling once. Beats 6-8: wobble, hands on the head, shake it off. Beats 9-10: back to the crouch. | L | 5.0 | A | The Capsule Post (03-TRANSPORT). Excursion 15. |
| 20 | Lamp Swing | D3.4 | The Night Inspector's waddle: short quick steps, knees bent and out, a very wide stance, the broad torso rocking 10 degrees from side to side. Both hands are cupped together above the head, fingers spread and wrists touching, as the lamp that is his head; the lamp tilts with the rocking. The right arm is the punch: it hangs long to the knee, and on beats 4, 8 and 12 it jabs forward at hip height with the hand clamping shut, while the lamp hands flare open. Head still inside the lamp hands. | L | 6.0 | A | The mini boss (07-ENEMIES, section 3). Excursion 25. |
| 21 | Bellows Breath | D3.5 | Beats 1-6: a slow whole-body inflate, arms rising out and up from the sides while the chest expands and the head tips back, heels lifting 4 cm. Beats 7-10: the collapse, arms dropping, knees bending, torso folding forward 25 degrees in a long exhale. Beats 11-16: the breath speeds up into a pant, two breath-in and collapse cycles of 3 beats each, shoulders pumping, ending half bent with hands on the knees. | L | 8.0 | A | The Bellows Vault (02-WORLD, zone 17). In place. |
| 22 | Shuffle | D4.1 | Expected: alternating heel-toe slides sideways at the clip's tempo, knees pumping loose, arms swinging opposite to the legs, head nodding on every second slide. Root travel removed so the feet slide on the spot. | L | 6.0 | M "Shuffling" | Default favourite. |
| 23 | Robot | D4.2 | Expected: isolated robotic moves: head ticks left and right, chest pops forward, upper and lower arm held in segments that move one joint at a time with hard stops on the beat; feet shuffle in place. | L | 6.0 | M "Robot Hip Hop Dance" | Pairs with Signal Arms for a two-player robot line. |
| 24 | Running Man | D4.3 | Expected: alternating knee drive to hip height while the other foot slides back; arms pump in running form (elbows at 90 degrees); a half hop each beat; head forward. In place. | L | 4.0 | M "Running Man" | Fits "they are not hungry, they are late" (01-LORE, section 1). |
| 25 | Trolley Push | D4.4 | Expected: both hands grip an imaginary cart handle at waist height and push forward and back; feet side-step two beats each way while the hips pop; shoulders turn to steer now and then. | L | 6.0 | M "Shopping Cart Dance" | Concourse dressing has a luggage trolley. |
| 26 | Raise the Roof | D4.5 | Expected: both arms bent, palms up at head height, pushed up 20 cm on every beat with a knee dip; head bobs; a step to the side every 4 beats. | L | 4.0 | M "Raise The Roof" | Pure party step; no melody needed. |
| 27 | Twist | D4.6 | Expected: feet pivot on the balls, heels sweep left and right, hips and knees twist 40 degrees each way, arms swing opposite to the hips at chest height; every 4 beats the dancer sinks 20 cm in a twist-down and returns over 4 beats. | L | 6.0 | M "Twist Dance" | Social step of the 60s, still played in 1984 roller discos. |
| 28 | Body Wave | D4.7 | Expected: a wave travels through the body: fingers, wrist, elbow, shoulder, chest, other shoulder, other arm, taking 2 beats each way; knees flex; head follows the wave. | L | 4.0 | M "Wave Hip Hop Dance" | The dance's own name; the calm Wave (41) keeps its name. |
| 29 | Locking | D4.8 | Expected: fast arm twirls ending in a lock (a freeze for 1 beat), a point to the floor, wrist rolls, a knee drop to a bent pose and back, a touch of the cap brim. | L | 6.0 | M "Locking Hip Hop Dance" | Locking family. |
| 30 | Swing | D5.1 | Expected: solo swing: rock step then triple step, Charleston kicks, knees knocking together, arms swinging in opposition, a hop at the end of each 8 beats. | L | 8.0 | M "Swing Dancing" | Solo swing, a social step of the 1940s that the clubs kept. |
| 31 | Samba | D5.2 | Expected: samba bounce: knees bob on a 1-a-2 count while the feet rock side to side, hip rolls, arms waving alternately above the head like flagging a train. | L | 6.0 | M "Samba Dancing" | The flag-waving reads as a rail signal. |
| 32 | Can-Can | D5.3 | Expected: hands hold the coat tails; a hop and a high kick (to chest height) alternating legs once per 2 beats; one long finishing kick on beat 11; shoulders back, chin up. | L | 6.0 | M "Can Can" | Conductor uniform joke (01-LORE, M2). |
| 33 | Soul Spin | D5.4 | Expected: step out on the left foot, a 360 degree spin on its ball with arms out, a drop with knees bent, a slide back with a clap on beat 4. | L | 4.0 | M "Northern Soul Spin" | A social step of the 70s clubs. |
| 34 | Chicken Dance | D5.5 | Expected: four 4-beat phrases: beaks (thumb and fingers of both hands snap together four times at the chin), wings (elbows pumped four times), tail (knees bent, hips wiggle four times, hands on hips), four claps; then it loops. | L | 6.0 | M "Chicken Dance" | Pure silly. Evokes an old party song, see risk 11. |
| 35 | Silly Dance | D5.6 | Expected: loose limbs: arms flail in opposite circles, knees lifted high, head loops, hips wobble, the dancer bounces side to side. | L | 6.0 | M "Silly Dancing" | Pure silly. |
| 36 | Hokey Pokey | D5.7 | Expected: right foot in, right foot out, in again and shake; then left foot, right arm, left arm, head, whole self: each part lifted, held out, shaken to the beat; a full turn at the end. | L | 8.0 | M "Hokey Pokey" | Participation dance. Evokes an old party song, see risk 11. |
| 37 | Windmill | D6.1 | Expected: low floor work: hands on the floor, legs sweep around the body in a circle (six-step footwork), body close to the floor. +in/out. Legs reach 45 units from the root. If no real windmill clip exists in the library and the verified clip is footwork, the clip is used and the name is changed to Six-Step at download. (decided here) | L | 6.0 | M "Breakdance Footwork" or "Flair" | Floor emote: the real hit volume stays upright (section 3.1). |
| 38 | Head Spin | D6.2 | Expected: entry kicks up to an inverted position on head and hands; loop: legs spread in a V, body spinning twice per second around the vertical axis, hands balancing. +in/out. Spread 40 units, height 54 units. | L | 4.0 | M "Headspin" | Floor emote. Needs 100 units of head room (section 3.1). |
| 39 | Freeze | D6.3 | Expected: entry drops into a freeze balanced on one hand and an elbow, legs crossed in the air; hold with a 2 cm sway and one foot tap on beat 5. +in/out. | L | 4.0 | M "Breakdance Freeze" | A held pose is the one dance that makes a good screenshot. |
| 40 | Uprock | D6.4 | Expected: standing footwork in a small circle (radius 40 units), burner arm swipes at chest height on every beat, a sharp jerk on beats 4 and 8, head level. | L | 6.0 | M "Bboy Uprock" | Standing breaking, so no in/out clip. |

### 2.2 Calm emotes, 41 to 65

| ID | Name | Page | Motion | L/S | Sec | Source | Note |
|---|---|---|---|---|---|---|---|
| 41 | Wave | centre | Right hand raised to head height, palm out, elbow bent 90 degrees; three side-to-side wags of 8 cm at 0.25 s each; one nod at the start; left hand relaxed. | S | 2.0 | M "Waving" | The default: centre of every page, played by an empty quick-use release. |
| 42 | Big Wave | C1.1 | Both arms raised overhead, three sweeps side to side over 2.4 s, the right arm 0.2 s ahead of the left; heels lifted. | S | 3.0 | M "Waving" mirrored to the left arm, A for the lift | Reads across a whole platform. |
| 43 | Transit Salute | C1.2 | Right hand flat, fingertips to the brow, elbow out 45 degrees, hold 0.8 s, snap down; heels together on the snap. | S | 2.5 | M "Salute" | The Transit Cop's salute (01-LORE, section 7). |
| 44 | Thumbs Up | C1.3 | Right fist forward at chest height, thumb up, pushed forward 6 cm; one nod. | S | 2.0 | A | Quick approval. Default favourite. |
| 45 | Slow Clap | C1.4 | Five claps 0.8 s apart; hands start 30 cm apart at chest height, each clap deliberate; slow nod between claps; chin up. | S | 4.0 | M "Clapping" retimed to 0.45 speed, A for the nods | Sarcasm without words. Default favourite. |
| 46 | Applause | C1.5 | Fast clapping, 4 per second for 3 s, at chest height; small knee bounce; one nod. | S | 3.5 | M "Clapping" | Honest approval, the opposite of 45. |
| 47 | Take a Bow | C1.6 | Right arm sweeps across the waist, left arm behind the back; torso bends 45 degrees over 0.8 s, holds 0.8 s, rises over 0.8 s. | S | 3.0 | M "Bowing" (verify), else A | The answer to a Slow Clap (45) or Applause (46). |
| 48 | Shrug | C2.1 | Shoulders rise 6 cm, elbows out, palms up at waist height, head tilts 12 degrees; hold 0.6 s, then drop. | S | 1.8 | M "Shrugging" (verify) | Disapproval and "no idea" in one. |
| 49 | Point | C2.2 | Right arm extends and holds 1.0 s with the index finger out; head turns toward the target. Three clips (forward, 30 degrees up, 30 degrees down) chosen by the view pitch at the moment of use; the body turns to the view yaw. | S | 2.0 | A (3 clips) | Direction. A live aim-offset does not exist (additive authoring is Missing, CC), so the target is approximated by three baked heights. Default favourite. |
| 50 | Come Here | C2.3 | Right hand beckons: palm up, four finger-curl pulls at 0.4 s intervals, the wrist drawing in; left hand on hip; head tilts toward the caller. | S | 2.5 | A | Direction, for the player who is lost. |
| 51 | Facepalm | C2.4 | Right palm slaps the forehead, head drops 15 degrees, holds 1.2 s, two slow head shakes, hand drops. | S | 2.5 | A | Disapproval, for the player who just pulled the wrong fuse. |
| 52 | Check Watch | C3.1 | Left forearm raised to chest height, right hand pushes the cuff back, a look of 0.8 s, a wrist shake, a second look, a tap on the dial. | S | 3.0 | A | Waiting; the station's stopped clocks read 23:47 (01-LORE, section 9). |
| 53 | Yawn and Stretch | C3.2 | Fingers interlaced overhead, palms up, 1.0 s; a big yawn with the head back 20 degrees and a hand to the mouth; shoulder rolls; relax. | S | 4.0 | CMU "common behaviors and expressions" (verify trial), else M "Stretching" | Waiting. |
| 54 | Sit Down | C3.3 | Sits cross-legged on the floor, hands on knees; rocks 3 degrees every 2 s; looks slowly left and right every 3 s. +in/out. | L | 4.0 | A | On the floor so no chair prop is needed. Default favourite. |
| 55 | Arms Crossed Lean | C3.4 | Weight on the left hip, right foot crossed over the left at the toe, torso leaning back 10 degrees, arms crossed high on the chest; every 3 s the weight shifts, the chin lifts and the head glances left then right. +in/out. | L | 6.0 | M "Standing Idle" arms-crossed variant (verify), else A | Leans on air, not on a wall, so it works anywhere. |
| 56 | Payphone | C3.5 | Right hand holds an imaginary receiver at the ear, left forearm across the waist; head nods every 1.5 s; one finger raised for "wait" at 3 s; left finger twirls an imaginary cord. +in/out (coin tap, lift the receiver; hang up). | L | 6.0 | M "Talking On Phone" (verify), cord twirl by A | Three pay phones stand in the station, each with its own event (01-LORE, section 11). |
| 57 | Read the Paper | C3.6 | Both hands hold an imaginary broadsheet at chest height, head down; every 3 s the right hand turns a page; a head tilt for "hm" at 6 s. +in/out (unfold; fold under the arm). | L | 8.0 | A | The 1985 commuter, the longest loop in the calm set. |
| 58 | Coffee Sip | C3.7 | Right hand holds a cup at chest height, raises it over 0.8 s, head tilts back 10 degrees, sip for 1.0 s, lowers, shoulders drop in an exhale. | S | 4.0 | M "Drinking" (verify) | The cup in the Announcer's Booth still steams (01-LORE, section 11). |
| 59 | Tie Shoelace | C3.8 | Kneels on the right knee over 0.7 s; both hands at the left shoe, two loops and a tug over 2.6 s; stands over 0.7 s. | S | 4.0 | A | The one gesture that looks like asking for trouble. Length at the 4 s limit. |
| 60 | Fist Pump | C1.7 | Right arm swings up, fist pumped overhead twice at 0.5 s intervals with a small hop; head up. | S | 2.0 | A (M "Victory" if verified) | Celebration, after a round. |
| 61 | High Five | C2.8 | Three clips. Offer (3.0 s hold): right arm raised, palm open at head height, elbow at 100 degrees, head turned toward the target, a small bounce. Contact (0.8 s): both players slap and recoil. Hang (1.2 s): if nobody answers, the arm lowers slowly with a shrug. | S | 3.0 + 0.8 + 1.2 | A (3 clips) | The only two-player calm emote (section 3.5). |
| 62 | Blow a Kiss | C1.8 | Right fingertips to the lips, then the hand sweeps out palm up as if throwing, head tilts 10 degrees, one shoulder up. | S | 2.2 | M "Blow A Kiss" (verify) | Greeting, warm. |
| 63 | Nod Yes | C2.5 | Head nods three times of 12 degrees at 0.3 s intervals, a slight shoulder lift. | S | 1.5 | M "Head Nod Yes" (verify) | Answer without chat. |
| 64 | Shake No | C2.6 | Head turns 20 degrees each way three times at 0.3 s intervals; right hand wags palm out at chest height. | S | 1.5 | M "Shaking Head No" (verify) | Answer without chat. |
| 65 | Laugh | C2.7 | Bent forward 15 degrees; belly pulses 6 times a second; head thrown back on every second pulse; right hand slaps the knee at 1.2 s; wipes an eye at 2.4 s. | S | 3.0 | M "Laughing" (verify) | Default favourite. |

### 2.3 Totals and clip count

- 65 emotes, **84 clips**: 65 base clips, plus 14 in/out clips (7 posture emotes: 37, 38, 39, 54, 55, 56, 57), plus 1
  Conga follower, 2 extra Point heights, 2 extra High Five clips (contact, hang). (decided here)
- Sources: 21 dances animated by us (A, rows 1 to 21), 19 library clips (rows 22 to 40), and the calm set as listed.
- Seconds: dance bodies 227.0 (originals 121.0, library clips 106.0), dance extras 9.4 (3 floor in/out pairs 5.4,
  follower 4.0), calm bodies 81.0, calm extras 13.2 (4 in/out pairs 7.2, Point 4.0, High Five 2.0). **Total 330.6 s of
  animation.**
- Family counts (for the owner's "no family more than three times" idea, met except once): breaking 4 (37, 38, 39,
  40), popping and locking 3 (23, 28, 29), the rest are below three. See the contradictions in section 9.

## 3. Rules of use

### 3.1 When an emote may start

An emote starts only if all of these are true. A refusal sends one private toast line (section 5.1, `maxis_n`)
in the player's language and nothing else happens.

- The player stands on the ground, is not downed and not in last stand.
- Not riding the Capsule Post capsule, not inside the Pack-a-Punch teleport sequence, not holding a quest item animation.
  Those chapters (`03-TRANSPORT.md`, `04-PAP-QUEST.md`) must set one flag, `self.iwz_busy`, for the duration; the
  emote code reads only that flag. (decided here)
- No map vote is open and the match is not ended (a vote or match end also cancels any running emote).
- The previous emote ended or was cancelled at least 1.0 s ago (cooldown, counted from the end). (decided here)
- **Edge test at the start** (decided here): eight ground traces on a ring of radius 60 units around the player, each
  must find floor within 48 units below the feet; otherwise the toast says "Too close to an edge". Reason: every
  emote fits inside a 60-unit radius, so this one test makes all 65 safe near ledges and track beds.
- Floor emotes (37, 38, 39, 54) also need no solid within 36 units to the side and 100 units overhead. (decided here)

### 3.2 When it stops

An emote cancels immediately on: move input, jump, fire, aim, weapon switch, reload, melee, taking damage, becoming
a revive target (last stand). A looping emote also ends when the wheel key is pressed again, when a map vote opens,
at match end and at disconnect. Posture emotes then play their out clip (0.8 s) before control returns; any other
cancel returns control at once.

How each cancel is read is part of proof P6: Fire, Aim, Melee and Use are proven readable by script (B, 3a);
velocity and view angles are proven; the damage notify is standard; reload and weapon switch calls are not in the
research. Controls stay live during an emote (they must, or no input could be read), so "move input" is detected as
velocity above 8 units per second or 4 units of displacement. If no reload or switch call exists, those two presses
do nothing because weapons are disabled, and the emote keeps going (accepted degradation). (decided here)

The Fire press that confirmed a wheel choice must not cancel the emote: cancel reading starts 250 ms after the
start and only after Fire, Aim and Melee have all been released once. (decided here)

### 3.3 No protection

Zombies attack the real player exactly as usual. The player's collision and hit volume stay where they were and stay
upright, even when the animation lies on the floor. The animation is cosmetic. Emoting does not reset the AFK timer
(AFK rules unchanged). (decided here)

### 3.4 Conga Car, joining

- A second player joins by pressing Use within 100 units behind the last dancer of the line, facing that dancer,
  with no other use target in range (door, buy). Up to 8 in the line, which is the eight-slot profile. (decided here)
- Slot k is 36 units behind slot k minus 1 along the leader's facing when the leader started. The joiner is slid
  there by script over 0.3 s (the real player entity moves; at most 150 units). The ground under the slot must pass
  the same edge test; if it does not, the join is refused.
- **Contradiction with the 60-unit rule, resolved:** a line of 8 is 252 units long. The 60-unit rule applies to each
  dancer's own animation, which has no root travel; the line shape comes from placement. (decided here)
- Phase: joiners wait in the follower pose (hands up, 0.5 s blend) until the leader's next 2-second cycle boundary
  (a shared clock `conga_t0`), so the wait is at most 2 s and everyone steps on the same beat. (decided here)
- If the leader stops, slot 2 becomes the leader at the next cycle boundary (switches to the leader clip) and the line
  continues; with one player left, it loops until cancelled. (decided here)

### 3.5 High Five

The first player plays Offer. A second player using High Five within 3.0 s, facing the first (within 45 degrees) and
between 36 and 84 units away, completes it: both slide to exactly 56 units apart over 0.25 s (each moves at most 28
units), both play Contact, both return to control. With no answer the first player plays Hang and stops. Outside the
distance window the second player gets the toast "Move closer". (decided here)

### 3.6 Weapon and camera

- The weapon is lowered or hidden when the emote starts and restored 0.25 s after it ends; no reload is triggered.
- **Camera:** on start the view pulls back over 0.3 s to a third-person orbit, 110 units behind and 24 up from the
  eye, pushed forward by collision (a trace from the eye to the wanted point, camera placed 8 units short of any hit).
  The player orbits with look input. On end it returns over 0.2 s. Other players see the full-body animation on the
  world model.
- If third person is not available (G4 failed, or the player set `.e cam off`, decided here), the player stays in
  first person and only others see the emote.
- Camera updates run at 20 Hz from a script entity (the vote's own thread rate). Whether that looks smooth for orbiting
  is not known; it is proof P5 and risk 5.

### 3.7 How the server plays it (one function for both pickers)

Candidate calls are named from general script knowledge and are **not in the research; each is to be proven**.

1. Validate (3.1). Set `self.paris_emote = id`.
2. Lower the weapon (candidate: `disableweapons`).
3. Spawn a rig: a script_model with the player's body model, play the `in` clip then the loop (candidate:
   `scriptmodelplayanim`), hide the real player from every client, link the rig to the real origin.
4. Start the camera (candidate: a script_origin with `cameralinkto`, moved every 50 ms from the player's view angles).
5. Each 50 ms tick: read cancel inputs (3.2), update the camera.
6. End: stop the clip, play `out` if the emote has one, delete the rig, unhide the player, return the camera over
   0.2 s, re-enable the weapon after 0.25 s. Free the rig on disconnect.

Entity cost is one rig per emoting player (at most 8) and one camera each, far below the Kino limits (about 240
extra visible entities, KINO). One manifest, `ops/emotes/emotes.json`, holds id, names in three languages, page and
wedge, seconds, loop flag, clip names, source and icon pose; the Lua table, the localization keys, the icon
generator, the test plan and the budget all read it, so no list exists twice. (decided here)

Animation names are delimited string literals (`emo_01_turnstile_hop`, `emo_01_turnstile_hop_in`) so they do not
grow Beast's canonical-string table (B, section 1.8; LOCALIZATION.md); the cold Beast capacity check is re-run once
when the module lands.

## 4. The wheel

### 4.1 Layout, in Maxis tokens

All values at the 1920 by 1080 canvas, scaled by the engine's `_1080p` factor (B, 1.3). Token values are copied from
`docs/MAXIS.md` and the Lua palette; the code is the source of truth if they ever differ by one unit (B, 1.2).

| Element | Value |
|---|---|
| Centre | (960, 540) |
| Dimmer | `void` `#07090C` at 55 % over the whole screen (the terminal's value) |
| Ring | outer radius 300, inner radius 120, 8 wedges of 45 degrees, wedge 1 centred at 12 o'clock, clockwise |
| Wedge panel | `panel` `#0D1218` at 90 % (the 86 to 94 % range of the panel token) |
| Separators | 8 spokes, 2 px, `line` `#22303D` |
| Hovered wedge | fill `panel-2` `#131B24`; outer arc `aether` `#34E8D2`, 4 px (radius 300 to 304); lifts 14 px outward in 120 ms; a glow copy of the wedge, `aether`, alpha 0 to 0.22 in 120 ms (the vote card's numbers) |
| Confirm flash | `amber` `#FFB238` on the chosen wedge for 80 ms |
| Favourite marker | small `amber` corner bracket, 2 px thick, arms 12 px, on the top-left corner of the wedge's icon box; built from two rectangles, no image (decided here) |
| Brackets around the wheel | `amber`, 2 px thick, arm 24 px (the terminal's arm length), on the square (628, 208) to (1292, 872), 8 px outside the lifted outer arc (decided here) |
| Page name | above the ring, centred at y 150, `MainExtended` 40, `bone` `#EEE7D7`, for example `STATION 1` |
| Page pips | below the ring at y 900, 10 pips of 12 by 12 px, pitch 18; current `aether`, others `line` (the vote's pip size) |
| Emote name | centre of the ring, `MainBold` 26 in `bone`; 22 and two lines when over 13 characters (decided here) |
| Category line | under the name, `MainCondensed` 18, `ash` `#8E949C`, for example `DANCE · STATION` |
| Footer hint | y 956, `MainCondensed` 18, `ash`, one line (localized) |
| Disabled or not shipped | icon and wedge in `ash`; a wedge with no shipped emote is not drawn (section 6.3) |

Wedge icon centres lie on radius 210 (the middle of the ring): wedge 1 (960, 330), 2 (1108, 392), 3 (1170, 540),
4 (1108, 688), 5 (960, 750), 6 (812, 688), 7 (750, 540), 8 (812, 392).

**Centre button and dead zone.** The dead zone is 12 % of the outer radius, so 36 px. A pointer inside it hovers
nothing, and the centre shows the Wave pictogram and the name "Wave". Releasing the key or clicking with the pointer
in the dead zone plays Wave. A pointer beyond the dead zone picks the wedge by direction alone, at any distance, so a
flick works without reaching the ring. (decided here)

### 4.2 Pages, all 65 placed

Wedge order is clockwise from the top. Wave (41) is the centre of every page. IDs in brackets.

| Page | Name (EN) | Wedge 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| F | FAVOURITES | Thumbs Up (44) | Slow Clap (45) | Point (49) | Turnstile Hop (1) | Rink Glide (4) | Shuffle (22) | Laugh (65) | Sit Down (54) |
| D1 | STATION 1 | Turnstile Hop (1) | Watch the Edge (2) | Third Rail Shimmy (3) | Rink Glide (4) | Conga Car (5) | Late Shift Shuffle (6) | Ticket Punch (7) | Signal Arms (8) |
| D2 | STATION 2 | Step Class '84 (9) | The Sprinkler (10) | The Lawnmower (11) | Pendulum (12) | Flap Board (13) | Yellow Line (14) | Dead Escalator (15) | Token Flip Strut (16) |
| D3 | STATION 3 | Rush Hour Squeeze (17) | Doors Closing (18) | Capsule Pop (19) | Lamp Swing (20) | Bellows Breath (21) | none | none | none |
| D4 | SOCIAL 1 | Shuffle (22) | Robot (23) | Running Man (24) | Trolley Push (25) | Raise the Roof (26) | Twist (27) | Body Wave (28) | Locking (29) |
| D5 | SOCIAL 2 | Swing (30) | Samba (31) | Can-Can (32) | Soul Spin (33) | Chicken Dance (34) | Silly Dance (35) | Hokey Pokey (36) | none |
| D6 | FLOOR | Windmill (37) | Head Spin (38) | Freeze (39) | Uprock (40) | none | none | none | none |
| C1 | CALM 1 · GREET AND CHEER | Big Wave (42) | Transit Salute (43) | Thumbs Up (44) | Slow Clap (45) | Applause (46) | Take a Bow (47) | Fist Pump (60) | Blow a Kiss (62) |
| C2 | CALM 2 · ANSWER AND POINT | Shrug (48) | Point (49) | Come Here (50) | Facepalm (51) | Nod Yes (63) | Shake No (64) | Laugh (65) | High Five (61) |
| C3 | CALM 3 · WAITING | Check Watch (52) | Yawn and Stretch (53) | Sit Down (54) | Arms Crossed Lean (55) | Payphone (56) | Read the Paper (57) | Coffee Sip (58) | Tie Shoelace (59) |

Check: D1 to D6 hold IDs 1 to 40 once each (eight wedges are left unused: three on D3, one on D5, four on D6; a
wedge with no shipped emote is not drawn anyway); C1 to C3 hold 42 to 65 once each; 41 is the centre. Page order in
the ring of pips: F, D1 to D6, C1 to C3, 10 pips. Reason for the grouping: the 21 originals come first, in three
STATION pages, so a new player finds the map's own dances before the library; the 19 library clips follow on
SOCIAL 1 and 2 and on FLOOR (the breaking family, kept on one page); calm pages follow the owner's coverage list
(greeting and approval, answer and direction, waiting).

### 4.3 Favourites

- Stored per player on the server, one small file per GUID in the same style as the language setting:
  `mods/paris_beta/emotes/<sanitized-guid>.txt` (fixed path, sanitized GUID, written only on change). One line:
  eight IDs separated by commas, 0 for an empty slot, then a pipe and the last-used ID.
  Default content: `44,45,49,1,4,22,65,54|41`. (decided here)
- Toggle on the hovered wedge. If the emote is not a favourite it goes to the first empty slot; if all 8 are taken,
  nothing changes and the toast says "Favourites full". Removing leaves a hole (the wedge is drawn empty, dimmed), so
  positions never shift under the player's thumb. (decided here)
- The centre is always Wave and cannot be a favourite slot.
- The last-used emote replays with a double tap of the wheel key (second tap within 300 ms). With no last-used
  emote it plays Wave.

### 4.4 Input

| Action | Mouse and keyboard | Controller |
|---|---|---|
| Open, quick | hold the wheel key at least 200 ms; release plays the hovered wedge; Esc cancels | hold the wheel button; release plays |
| Open, browse | tap the key (under 150 ms): the wheel stays open; click plays; tap again or Esc closes | tap; A plays; B closes |
| Pick a wedge | direction of the pointer from the centre, dead zone 36 px | right stick direction, dead zone 12 % of the stick range |
| Change page | mouse wheel, or Q and E | left and right bumpers |
| Favourite | right click on the hovered wedge, or F (decided here) | Y |
| Confirm | left click, or release in quick mode | A |
| Close | Esc, or tap the key again | B |
| Replay last | double tap of the key | double tap of the button |

Default key (decided here): `B` on the keyboard and D-pad down on the controller, rebindable. Collisions with stock
binds are not stated in the research and are the first check in proof P4. After a tap the wheel's open animation is
held back 150 ms, so a double tap replays the last emote without a visible flash.

### 4.5 Icons

One 96 px pictogram per emote, in `bone`. Rules: 3 px stroke, no fill, one continuous single-stroke figure (head a
circle of 14 px, spine, limbs as straight segments with round caps and joins), 8 px margin inside the 96 px square,
and **one accent dot**, an 8 px filled `amber` dot on the end of the moving limb (hand or foot; the head for the
nods). In the wheel: `bone` figure, `amber` dot, `ash` for the whole icon when the emote is not shipped.

The pictogram is generated from the emote's own clip, not drawn by hand (decided here): the manifest names the key
frame (the frame furthest from the neutral pose), the generator projects the skeleton to 2D (front view, or side
view when the depth of the motion is larger), draws the figure by the rules above and places the dot on the limb with
the largest travel. Reason: the icon cannot disagree with the animation, and a changed clip regenerates its icon.
The generator runs offline, like `ops/maxis/make_art.py`, and the art is not committed (the generator is).

Shipping: the 65 icons are one atlas material if a Lua image can show a sub-rectangle (not stated in the research;
proof P4), else 65 small materials of 96 by 96 built by the existing 2D material recipe (`Build-ParisMod.ps1:267-301`).

### 4.6 Wheel animation and sound

| Event | Motion |
|---|---|
| Open | ring scales 92 % to 100 % and fades in over 120 ms; wedges start 10 ms apart, clockwise from wedge 1 |
| Page change | the icon and name layer rotates 22.5 degrees (icons travel on a straight chord, 82 px at radius 210) while cross-fading over 100 ms; the wedge base does not turn, it is symmetric |
| Confirm | the chosen wedge flashes `amber` for 80 ms; the wheel closes in 100 ms |
| Close | fade out over 100 ms |

Rotation and arcs are not among the documented Lua primitives (B, 3b); that is why the page change is a chord slide plus
cross-fade, and why the wedges are images (4.7). Easing is not defined in Maxis; linear until a reviewer asks otherwise.

**Sound is not defined anywhere in Maxis** (B, 1.7). Todo for the audio chapter (`11-AUDIO-DIRECTION.md`), three
short sounds, in the station's vocabulary, none taken from another product:

| Sound | Length | Character |
|---|---|---|
| open | about 180 ms | a relay click followed by a soft rising two-note chime, quieter than the Three-Tone |
| hover tick | about 20 ms | one mechanical relay tick, at least 8 dB below the open sound, so a sweep across 8 wedges is not loud |
| confirm | about 120 ms | a ticket-punch "ka-chunk", the same punch that is dance 7 |

Until the chapter lands the wheel is silent. How a UI sound is played from Lua is not stated; first task of the audio chapter.

### 4.7 Art the Lua wheel needs

Because the Lua primitives have no arc (B, 7), the wheel ships as white masks tinted by `SetRGBFromInt`, so one image
serves every colour in the table: `maxis_wheel_ring` (annulus), `maxis_wheel_spokes` (the 8 separators),
`maxis_wheel_sector_0` to `_7` (the hover fill) and `maxis_wheel_arc_0` to `_7` (the 4 px outer arc): 18 images. The glow
is the sector image scaled to 104 %. The images come from one generator, with the Maxis recipe for 2D materials.

## 5. Delivery, honestly

Two tiers. They end in the same server function (3.7). The server decides; nothing the client sends is trusted
beyond an ID in range.

### 5.1 Tier 1: the Lua wheel (section 4 as designed)

**Who gets it.** Only clients that load Lua from a mod: lab clients, the owner's native build, any build from the
client project's `develop`. The official updater client (v1.1.0, 26 Sep) does not load zone Lua. It will when the
merged change (client project PR 697, merged to `develop` 30 Sep) is released; checked 10 Nov, not released. Nothing
is posted upstream (B, 3b). Players on the official client use Tier 2.

**Choice from client to server.** The client sends an index through `Engine.NotifyServer(name, value)`. Names are an
index into a fixed retail table, so only four retail names are reusable: `intel_tab`, `map_select`, `boss_set`,
`boss_reset`, already used by Maxis (B, 3b). **The 15-index limit:** the research says 15 indices per `boss_set` and
the server ignores an index above 15 (`UIGSC:290`). That check is in our own handler; the research does not show it
is an engine limit, and the engine's range for the value is not stated. The design therefore stays inside 1 to 15.

Encoding (decided here). Channel `intel_tab` (the handshake name: value 1 stays the handshake, so no menu action can
be triggered by a stray wheel message). Values 2 to 15 belong to the wheel. An emote ID 1 to 65 needs 7 bits; two
digits in base 14 carry it (hi 0 to 4, lo 0 to 13, ID = hi times 14 plus lo plus 1, max 65 = hi 4, lo 8).

| Value | Meaning |
|---|---|
| 1 | handshake, unchanged |
| 2 to 6 | PLAY, high digit 0 to 4 (value = 2 + hi); the next message is the low digit |
| 7 to 11 | FAVOURITE toggle, high digit 0 to 4 (value = 7 + hi); the next message is the low digit |
| 12 | REPLAY the last-used emote |
| 13 | CLOSE (nothing chosen; clears any pending digit) |
| 14, 15 | spare |
| 2 to 15 after an opcode | the low digit (value = 2 + lo, lo 0 to 13) |

The server keeps one pending opcode per player for 1.0 s; the next value in that window completes it. A new opcode
replaces a pending one. An ID outside 1 to 65, an unshipped ID, or a state refusal (3.1) is dropped with a toast.
The client resolves page and wedge to an ID itself, because the server sends it the favourites (below).

Two pitfalls found in the research, both in our own server code, neither needing an engine change:
1. The shared handler ignores a second event inside 400 ms (`UIGSC:290`). The two messages of a frame arrive
   together, so the emote branch must run before that gate. If it cannot, the client spaces the two messages 420 ms
   apart, which costs the 150 ms latency target; then the one-message form below is needed.
2. The terminal's `intel_tab` handler must test for value 1 and ignore 2 to 15.

**One-message upgrade, to prove first (P3):** send values 16 to 127 and 1000 from a lab client and read what the
server's `luinotifyserver` receives. If the value arrives intact, one message carries the whole choice: value =
opcode times 128 plus ID (PLAY 1, FAVOURITE 2, REPLAY 3, CLOSE 4). Then the two-digit scheme is retired.

**Server to client.** A sixth Maxis dvar, `maxis_e`, written with `setclientdvar`, stamped with the server time like
the other five and dropped by the client if stale (B, 3b): `t|until|seq|lang|fav|last|mask|cam`. `fav` = 8 IDs
separated by commas, `last` = one ID, `mask` = three 24-bit hexadecimal words (bit i = emote i + 1 is shipped),
`cam` = 0 or 1. About 70 bytes, no newline, quote or percent sign, `|` between fields. Written only on change (join,
favourite change, language change, wave shipped), so at most a few writes per player per session, well inside the
24 writes per 10 seconds and the 128-entry reliable ring (B, 3b; SERVER-COMMAND-OVERFLOW).
The wheel itself needs no server state to open; a refused emote returns a toast line through the existing `maxis_n`.

**Hit testing.** The Lua tier needs the pointer angle. Whether Lua exposes the cursor position or lets it be
re-centred is not in the research. Three cases, in order of preference (decided here):
1. Cursor coordinates available: exact angle maths, as in 4.1.
2. Coordinates not available: a 16 by 16 grid of transparent buttons (about 38 px each) over the 600 px square;
   each cell stores the wedge of its centre; cells within 8 degrees of a wedge boundary are neutral (they do not
   change the highlight), which gives the hysteresis that a 38 px cell cannot give at radius 120.
3. The cursor cannot be placed at the centre: the ring is drawn centred on the cursor position at open, clamped to the
   screen.

**Open path B, works without Lua key capture.** Key capture in Lua is unproven, and it is the first thing to prove (P4).
Without it, a key the player binds to `say .e` (Tier 2's command) makes the server write `maxis_e` with an "open"
flag; the Lua polls its dvars every 100 ms (as Maxis does) and opens the wheel. That is tap-to-open only; hold and
release cannot work through chat, because chat has no key-up.

**Not shown in the research and therefore unproven for Tier 1:** key capture, gamepad stick and button events (Maxis
has no gamepad focus navigation, B, section 4), cursor warp, image sub-rectangles, whether a wedge fill can be tinted
at runtime (the vote does tint `white` rectangles, an image tint is the same call but not exercised).

### 5.2 Tier 2: the server-drawn wheel, for every player today

No client change, no download for the picker. Opened by the chat command `.e` (a player binds a key to `say .e`),
so this works on the official client.

| Command | Result |
|---|---|
| `.e` | opens the wheel on the last used page; opens a second time inside 400 ms = replay last; opens while open = closes |
| `.e <name or number>` | plays directly; number = ID 1 to 65; name = a unique case-insensitive fragment in the player's language or in English |
| `.e fav <n>` | plays favourite slot 1 to 8 |
| `.e fav set <n> <name or number>` | puts an emote in slot n (decided here) |
| `.e cam on` or `.e cam off` | third-person view on or off, saved per player (decided here) |

**The wheel is a ring of text labels around the screen centre.** Stock materials only (`white` rectangles), the
engine default font, `fontscale` as the other Maxis HudElem panels. The owner's list is 12 elements: 8 labels, the
highlight bar, the title, the page-pips text, the hint. **A 13th is added, the centre label** (the Wave
button), so the dead zone reads as a choice: **13 elements**. The map's one HUD allocator (`09-TAB-AND-HUD.md` section 3) holds
the 24 in this state as wheel 13, counter 5, and H2 and H4 if active (3), **21 in all**, and releases H1, H3 and
H5 to H9 while the wheel is open (decided here). Allocation order is admission priority (B, 1.8): the 8 labels, the highlight, the centre label,
the title, the pips, the hint last. Elements are destroyed on close, not hidden, and marked `archived = false`.

| Element | Place (HudElem units from centre) | Content |
|---|---|---|
| 8 labels | N (0,-110), NE (150,-78), E (200,0), SE (150,78), S (0,110), SW (-150,78), W (-200,0), NW (-150,-78) | emote name, `fontscale` 1.0, centred |
| highlight bar | on the picked label, 150 by 20 | `white` rectangle, `aether`, alpha 0.35; moved by setting x and y |
| centre label | (0,0) | `Wave`, shown dimmed; bright when in the dead zone |
| title | (0,-150) | `STATION 1`, `fontscale` 1.1 |
| pips | (0,150) | ten marks, for example `^5●^7 ○ ○ ○ ○ ○ ○ ○ ○ ○`; `^5` aether for the current page |
| hint | (0,172) | `FIRE play  AIM page  USE favourite  MELEE close`, `fontscale` 0.7, localized |

**Pointer** (the vote's virtual cursor, in two dimensions): when the wheel opens, store the view yaw0 and pitch0. Each
20 Hz tick, dyaw = wrap180(yaw minus yaw0), dpitch = pitch minus pitch0; magnitude m = square root of dyaw squared
plus dpitch squared. If m is under 3 degrees the pointer is in the dead zone (Wave). Otherwise the angle clockwise from
up is phi = atan2(minus dyaw, minus dpitch), wedge = floor((phi + 22.5) modulo 360 divided by 45) + 1. A wedge changes
only when phi is more than 4 degrees past a boundary (hysteresis). If m exceeds 24 degrees the anchor follows, so the
pointer saturates instead of running away (the vote's edge re-anchor). If the view at open is within 25 degrees of the
pitch limit, the anchor is moved to a safe pitch. (decided here)

**Controls.** Fire confirms (Fire is accepted only after it has been released once since opening, so a player
shooting when the wheel opens does not confirm by accident), Aim = next page (wraps), Use = toggle favourite on the
highlighted wedge, Melee closes. The wheel closes itself after 8 s of no input. Priority: a map vote blocks it, and
opening it closes a private page or the terminal first (the vote already has priority over every private panel).

**Movement frozen while open.** The owner's decision. The research proves only `freezecontrols`, which also freezes
look, and the vote uses `freezecontrols(false)` so the view can move (B, 4). A movement-only freeze is therefore
**unproven**; candidates are `allowmovement(false)` or a velocity clamp. Proof P7. If none works, the wheel does not
freeze and instead closes when the player moves more than 24 units or takes damage (decided here).

Cost: every distinct label is an engine string: 65 names and 12 UI texts in up to 3 languages is under 250 strings
ever. The names go through the localization generator as delimited literals (6.1), so the identifier table of Beast
does not grow.

### 5.3 Where the clips live

The 84 clips go in the mod zone `mods/paris`, so every map that runs the mod can use them, and the official client
downloads them by itself with the rest of the mod (CCOMP, KINO; only `mod.ff`, `.sabl`, `.sabs` travel, one mod zone).
If Station Zero's server does not run `fs_game mods/paris`, the clips go in the map's own zone instead, which only
that map can use and whose delivery by a dedicated server is itself unproven (N6, A section o). The mod is
downloaded whole when its hash changes and a failed download terminates the official client (A, section o; fork fix
not upstream).

## 6. Localization, EN, FR, ES

Every label is shown in the player's language (`.lang`, saved per GUID). Server-drawn text goes through
`config/localization.json` and `ops/Generate-Localization.py` (placeholders, delimited literals); Lua text goes in
the `COPY` table. Names may be adapted, not translated literally, and are kept short. Rendered accented glyphs on a
real client are not yet established (B, section 5), so names use accents only where the language needs them; proof
P9 checks é, è, ñ, ¿ and ¡ on a real client before the strings ship.

### 6.1 Pages and interface texts

| Key | EN | FR | ES |
|---|---|---|---|
| F | FAVOURITES | FAVORIS | FAVORITOS |
| D1 | STATION 1 | STATION 1 | ESTACIÓN 1 |
| D2 | STATION 2 | STATION 2 | ESTACIÓN 2 |
| D3 | STATION 3 | STATION 3 | ESTACIÓN 3 |
| D4 | SOCIAL 1 | SOIRÉE 1 | FIESTA 1 |
| D5 | SOCIAL 2 | SOIRÉE 2 | FIESTA 2 |
| D6 | FLOOR | SOL | SUELO |
| C1 | CALM 1 · GREET AND CHEER | GESTES 1 · SALUER ET FÊTER | GESTOS 1 · SALUDAR Y ANIMAR |
| C2 | CALM 2 · ANSWER AND POINT | GESTES 2 · RÉPONDRE ET MONTRER | GESTOS 2 · RESPONDER Y SEÑALAR |
| C3 | CALM 3 · WAITING | GESTES 3 · ATTENTE | GESTOS 3 · ESPERA |
| hint, Tier 2 | FIRE play  AIM page  USE favourite  MELEE close | TIR jouer  VISÉE page  UTILISER favori  CAC fermer | DISPARO usar  APUNTAR página  USAR favorito  CUERPO fin |
| hint, Tier 1 | CLICK play  Q E page  F favourite  ESC close | CLIC jouer  A E page  F favori  ÉCHAP fermer | CLIC usar  Q E página  F favorito  ESC cerrar |
| toast, not now | Emotes: not now | Emotes : pas maintenant | Emotes: ahora no |
| toast, cooldown | Emotes: wait a second | Emotes : une seconde | Emotes: un segundo |
| toast, edge | Too close to an edge | Trop près du bord | Demasiado cerca del borde |
| toast, full | Favourites full | Favoris pleins | Favoritos llenos |
| toast, closer | Move closer | Rapproche-toi | Acércate |

Two cells are not final: the ES melee word in the Tier 2 hint is cut to fit one line and is shortened again after the
first frame check; the FR keyboard hint uses A and E on an AZERTY layout (Q and E on QWERTY), which the Lua
decides from the keyboard layout if it can read it, else shows the Q and E of the stock default (not stated).

### 6.2 Emote names

| ID | EN | FR | ES |
|---|---|---|---|
| 1 | Turnstile Hop | Saute-tourniquet | Salto del torniquete |
| 2 | Watch the Edge | Attention au bord | Cuidado con el borde |
| 3 | Third Rail Shimmy | Frisson du rail | Temblor del riel |
| 4 | Rink Glide | Roller disco | Patines disco |
| 5 | Conga Car | Wagon conga | Vagón conga |
| 6 | Late Shift Shuffle | Fin de service | Fin de turno |
| 7 | Ticket Punch | Poinçon | Picar el billete |
| 8 | Signal Arms | Bras de sémaphore | Brazos de semáforo |
| 9 | Step Class '84 | Cours de step 84 | Clase de step 84 |
| 10 | The Sprinkler | L'arroseur | El aspersor |
| 11 | The Lawnmower | La tondeuse | El cortacésped |
| 12 | Pendulum | Pendule | Péndulo |
| 13 | Flap Board | Tableau à clapets | Panel de lamas |
| 14 | Yellow Line | Ligne jaune | Línea amarilla |
| 15 | Dead Escalator | Escalator en panne | Escalera averiada |
| 16 | Token Flip Strut | Jeton lancé | Ficha al aire |
| 17 | Rush Hour Squeeze | Heure de pointe | Hora punta |
| 18 | Doors Closing | Fermeture des portes | Cierre de puertas |
| 19 | Capsule Pop | Capsule éjectée | Cápsula disparada |
| 20 | Lamp Swing | Lampe balancée | Farol oscilante |
| 21 | Bellows Breath | Souffle du soufflet | Aliento del fuelle |
| 22 | Shuffle | Shuffle | Shuffle |
| 23 | Robot | Robot | Robot |
| 24 | Running Man | Running Man | Running Man |
| 25 | Trolley Push | Poussée de caddie | Empujar el carrito |
| 26 | Raise the Roof | Lève le toit | Arriba el techo |
| 27 | Twist | Twist | Twist |
| 28 | Body Wave | Vague du corps | Ola corporal |
| 29 | Locking | Locking | Locking |
| 30 | Swing | Swing | Swing |
| 31 | Samba | Samba | Samba |
| 32 | Can-Can | Cancan | Cancán |
| 33 | Soul Spin | Tour soul | Giro soul |
| 34 | Chicken Dance | Danse du poulet | Baile del pollito |
| 35 | Silly Dance | Danse folle | Baile loco |
| 36 | Hokey Pokey | Hokey Pokey | Hokey Pokey |
| 37 | Windmill | Moulin à vent | Molino |
| 38 | Head Spin | Toupie | Giro de cabeza |
| 39 | Freeze | Freeze | Congelado |
| 40 | Uprock | Uprock | Uprock |
| 41 | Wave | Coucou | Hola |
| 42 | Big Wave | Grand coucou | Gran saludo |
| 43 | Transit Salute | Salut du métro | Saludo del metro |
| 44 | Thumbs Up | Pouce levé | Pulgar arriba |
| 45 | Slow Clap | Applaudissement lent | Aplauso lento |
| 46 | Applause | Applaudir | Aplauso |
| 47 | Take a Bow | Révérence | Reverencia |
| 48 | Shrug | Haussement d'épaules | Encogerse |
| 49 | Point | Montrer du doigt | Señalar |
| 50 | Come Here | Viens ici | Ven aquí |
| 51 | Facepalm | Main au front | Mano a la cara |
| 52 | Check Watch | Regarder l'heure | Mirar la hora |
| 53 | Yawn and Stretch | Bâiller, s'étirer | Bostezo |
| 54 | Sit Down | S'asseoir | Sentarse |
| 55 | Arms Crossed Lean | Adossé | Apoyado |
| 56 | Payphone | Cabine | Teléfono público |
| 57 | Read the Paper | Lire le journal | Leer el diario |
| 58 | Coffee Sip | Gorgée de café | Sorbo de café |
| 59 | Tie Shoelace | Nouer un lacet | Atarse el cordón |
| 60 | Fist Pump | Poing levé | Puño al aire |
| 61 | High Five | Tope là | Chócala |
| 62 | Blow a Kiss | Bisou | Beso |
| 63 | Nod Yes | Oui de la tête | Decir sí |
| 64 | Shake No | Non de la tête | Decir no |
| 65 | Laugh | Rire | Reír |

Category lines under the name use the page key: for example `DANCE · STATION`, `DANSE · STATION`, `BAILE · ESTACIÓN`.
FR and ES column strings are written once in the manifest, and both delivery tiers read them from it.

### 6.3 What the wheel shows before every clip exists

`maxis_e.mask` lists the shipped IDs. A wedge whose emote is not shipped is not drawn; a page with no shipped emote
is skipped when paging. In wave 1 (section 7) the wheel therefore shows the FAVOURITES page, plus the pages whose
wedges are partly filled by the 9 shipped emotes. (decided here)

## 7. Budget and the two waves

**All figures below are estimates, to be measured.** No full-body clip of ours exists yet.

- **Animation.** Typical compressed full-body clips of this kind run in the order of 5 to 12 KB per second (assumed
  about 100 joints, 30 fps, quantised rotations, key reduction). Measure it before relying on it: the stock
  full-body clips are in the zone and the xanim codec reads all 4,029 Spaceland animations (A, section n), so the
  mean KB per second of a sample of stock clips of the same skeleton gives the real number in minutes.
  330.6 s at 5 to 12 KB/s is **1.7 to 4.0 MB, midpoint about 2.8 MB**, doubled if the heroes need two skeletons.
- **Art.** The wheel's 18 white masks (section 4.7) are about 0.8 MB at 8 bits per pixel and about 3.4 MB as
  RGBA before the zone's own storage; icons are about 2.4 MB as RGBA (65 by 96 by 96 by 4). Stored size is not
  known; the measured reference is the existing Maxis art (256 by 256 and 256 by 512 TGA materials).
  Estimated 1 to 6 MB.
- **Whole feature:** about 3 to 10 MB in the mod zone. For comparison, the BO3 weapons mod is 29.9 MB combined (A, section o).

| Wave | Contents | Clips | Seconds | Animation size (5 to 12 KB/s) |
|---|---|---|---|---|
| 1 | Wave (41) and the 8 default favourites: 44, 45, 49 (3 Point clips), 1, 4, 22, 65, 54 (with in/out) | 13 | 44.8 | 0.22 to 0.54 MB |
| 2 | the other 56 emotes | 71 | 285.8 | 1.4 to 3.4 MB |

Wave 1 plus the wheel art makes a complete, small feature that proves the whole chain on 9 emotes. Wave 2 is the
same chain repeated, so its risk is volume, not novelty. The mod is downloaded whole when its hash changes, so wave 2
is a second full download for every player, at the measured 5.4 to 8.6 MB/s of the Canada host, and the server needs
a controlled restart or a versioned mod path because it caches advertised hashes (A, section o). That is the price
of two waves; the alternative, one wave, delays the proof of the chain until all 84 clips exist.

## 8. What closes the emote feature

Each item is a measurement, not an opinion. No visual claim is made before independent reviewers have judged real
frames (project rule), and captures are measured for validity first.

| Proof | How | Pass |
|---|---|---|
| P1 | C1 lands: every stock animation through glTF and back within its tolerance | C1's own pass |
| P2 | **Bone error against the source (C2).** One of our clips played in the game, bone positions read back per frame and compared with the clip as retargeted in Blender, per bone | at most 1.0 degree of rotation and 1 unit of position on end bones, on every frame. C2 may tighten it. (decided here) |
| P3 | Notify value range: values 16 to 127 and 1000 through `luinotifyserver` from a lab client | the received value equals the sent one, else the two-digit scheme stays |
| P4 | Lua tier inputs on a lab client: key capture, key release, cursor position or warp, gamepad stick and buttons, image sub-rectangle, tinted images | each answered yes or no; wheel opens by key and by `say .e` |
| P5 | G3 and G4 in the game: a rig plays a clip, a second client sees it, the owner's view orbits it; camera feel at 20 Hz | frames from both clients; no visible stepping in a frame sequence |
| P6 | Cancel causes: a plan triggers each of the 9 cancel inputs and reads the state | each cancels within 100 ms; weapon back within 0.25 s after |
| P7 | Movement-only freeze for Tier 2 | one candidate call works, or the fallback close-on-move is used |
| P8 | **A plan plays each of the 65 emotes and reads back the animation state.** Headless on a private server with a bot (about 40 s), one plan, written expectations | for all 65: state is playing within 150 ms of the command; duration within 5 % of the table's Sec; clean end; weapon restored; rig deleted; entity count back to the start. Includes the 3 Point clips, the Conga join of 8 bots, High Five with 2 bots, the edge refusal and the cooldown refusal |
| P9 | Frames of 5 emotes judged by independent reviewers, full-resolution frames, measured for validity first. The five: Rink Glide (original, spin), Shuffle (retargeted library clip), Windmill (floor), Sit Down (loop with in and out), High Five (two players) | every reviewer says the pose reads and nothing clips or floats; no reviewer sees the real player body through the rig |
| P10 | **Wheel layout checked by the UI-as-data tool (U1)** for overlap, clipping and off-screen: all 10 pages, 3 languages, the longest names, 16 by 9 plus 16 by 10 and 21 by 9 | zero overlaps between wedge labels, icons stay inside their wedge, the longest name fits the centre in two lines, nothing off-screen. Plus a frame of FR and ES showing accents |
| P11 | **Input latency, key to animation start.** A client plan sends the key, the server logs the start of the clip, the client reports the frame where the pose changes | under 150 ms on loopback; at a 60 ms ping the target is 150 ms plus the ping, which the network share cannot be removed from (netlab) |
| P12 | Size: measured mod size before and after each wave | within the section 7 estimate, or the estimate is corrected here |
| P13 | Both tiers on the same plan: every emote reachable from the wheel in each tier, favourites persist across a reconnect | per-GUID file read back |

U1 is running, not landed (A); P10 waits for it, the other proofs do not.

### Risks

1. **No emote exists before G1 to G4.** The unproven pair (G3 world-model animation, G4 third person) can each fail.
2. **Reach of Tier 1.** Players on the official client have no Lua wheel until the client project releases its
   merged change. Tier 2 is the only no-download path. Owner decision needed before posting anything upstream; the
   research says nothing is posted.
3. **Key capture, cursor and gamepad in Lua are unproven;** the fallback paths (chat key, grid of buttons) cost the
   hold-and-release quick use or the exact angle.
4. **The rig route.** Hiding the real player may also hide its name tag, revive prompt, kill-cam, ping marker or
   weapon sounds; the rig may not be lit like a player (a known dark-model issue exists for IWZ machine models,
   A section 4). Each is a P5 frame to look at.
5. **Camera feel.** A server-moved camera at 20 Hz may feel laggy when orbiting. The camera dvar route is probably
   closed (inference from the ignored `cg_fov`).
6. **Skeletons.** Four hero bodies may not share one skeleton; the female hero's body may differ.
7. **Retargeting quality.** Mixamo rigs have different proportions from the game's; hands and elbows can break. P2
   measures against the retargeted source, so a bad retarget is invisible to P2 and caught by P9.
8. **Server writes.** `maxis_e` and toasts add reliable commands; they are on-change and capped, but the overflow
   class of disconnect is unresolved (B, section 6, item 6).
9. **Mod size and a second download** (section 7); a failed download terminates the official client (fork fix only).
10. **Accents** in HudElem text are not established on a real client (P10 frame).
11. **Two dances evoke old party songs** (Chicken Dance, Hokey Pokey). Both are short traditional participation
    dances and the clips are licensed Mixamo assets, but the rule is "no long choreography tied to one song". The
    owner chose both; the risk is recorded, not changed.
12. **Mixamo terms** can change; the record kept at download (section 1) is the evidence.
13. **Safety by the edge test** only checks 8 points; a very thin walkway could pass the test and the animation could
    still clip a railing. Reviewer frames (P9) include one near a wall.
14. **AFK and the wheel:** a looping emote left running is an AFK; rules unchanged (3.3).

## 9. Decisions made here, and conflicts found

The 40 dances, 25 calm emotes, the wheel look and all rules in sections C and D of the brief are used as given. The
items marked "(decided here)" fill gaps in the same spirit. Conflicts between the brief and the research:

1. **The 15-index limit** is in our own handler, not shown to be an engine limit, and a 400 ms gate in the same
   handler would swallow the second message of a two-message choice (5.1).
2. **12 HUD elements** leave no place for the centre label of the Wave button; 13 are used (5.2).
3. **Movement frozen, look free** is not a proven call; `freezecontrols` freezes both (5.2).
4. **A Conga line of 8** is 252 units long against a 60-unit radius; resolved as per-dancer radius (3.4).
5. **Point at the crosshair** needs an aim-offset blend, and additive authoring is Missing; three baked heights are used.
6. **"No family more than three times"** is met except for breaking, which has 4 (popping and locking is down to 3).
7. **Two song-tied dances** (Chicken Dance, Hokey Pokey) sit against the rule on songs.
8. **Third person** cannot rely on a client dvar (the client ignores a server `cg_fov`).


## Notes added after review (binding)

- **Where the clips ship.** Read every mention of "the mod zone" in this chapter as a recommendation to the
  owner, not a plan: a change to the servers' global mod makes every player of every map download it again, and
  a failed download closes today's official client. The default is to ship emotes with Station Zero's own zone;
  offering them on every map through the global mod is the owner's deployment choice once the client's download
  failure is fixed (package CF3a).
- **HUD elements.** The server-drawn wheel's 13 elements are granted by the map's one HUD allocator
  (`09-TAB-AND-HUD.md` section 3): while the wheel is open the allocator holds the wheel's 13, the counter's 5 and H2 and H4 if active (3), 21 in all, and releases the rest.
- **A hidden real player** (third-person rig): zombies keep targeting the player and hits land on the player's
  real collision; the rig is only what is drawn. Taking damage cancels the emote, as stated.
- **First probe, now**: package M0 plays a *stock* full-body clip on a real player's world model, seen by a
  second client, and tries a third-person view. It needs none of our animations and decides early whether the
  client fork is needed (CF4).
- **Families.** The set has four breaking clips, one over the "three per family" intent (popping and locking is
  down to three). Kept on purpose: breaking is one of the two families players ask for most, and the wheel groups it
  on its own FLOOR page. "Chicken Dance" and "Hokey Pokey" are folk party dances with no music attached; the library
  clips' terms are recorded at download and either is replaced by an original if its terms forbid redistribution.
- A Conga joiner slides only themselves, and only onto a slot with no enemy within 200 units.
