> **Note (11 Nov 2026):** the "hybrid crowd" in this document is withdrawn. The crowd module was removed on 11 Nov 2026 because script-moved bodies are not real zombies; real capacity is engine work (server repository docs/ZOMBIE-CAPACITY.md).

# 14 · WHAT THE PLAYER'S GAME MUST BE ABLE TO DO

Owner's principle (11 Nov 2026): everything must be playable by real players on the public servers, with good
performance, quality and clarity. Where the official client lacks something a feature needs, the answer is
not a lab-only trick: the capability is planned as its own package in the project's fork of the client
(`maxis0191/iw7-mod`), kept clean and minimal so it can be proposed to the client project later. Nothing is
posted there now. Until a capability is in players' hands, each feature gives a player on today's official
client a graceful fallback: never a crash, never a broken screen.

This page says, for each feature of the map, which capability it needs and what that player gets meanwhile.
Packages CF1 to CF5 are in `12-BUILD-PLAN.md` section 2b. Order: CF3a, CF1, CF5, CF3b, CF4 (if needed), CF2.
Where this page says what should or should not be offered on public servers, it is a recommendation: placing a
map in a rotation, slot counts and server profiles are deployments, and deployments are the owner's.

## 1. Capabilities

| # | Capability | State in the official client today | Package |
|---|---|---|---|
| 1 | **Lua screens from a downloaded zone**, with named client-to-server events and a registrable key | not in the released client (v1.1.0). The loading part was merged in the client project's development line on 30 Sep and is unreleased. Named events and key registration do not exist: only four retail event names can be reused, and no key handler exists | CF1 |
| 2 | **More than 24 zombies as real agents** (96 agent records, in server and client) | fixed tables around 24; a server with larger tables is incompatible with the official client | CF2. Said plainly: this one is **not** a small change (agent pools, character tables, corpse and entity boundaries, network field widths, in two programs). It is kept as clean as its nature allows and is the last of the fork packages |
| 3a | **A failed download returns to the menu with a message**, for the mod and for a map | today a failed download closes the client. This already threatens every player whenever the servers' mod changes | **CF3a, the first fork package**: the smallest change, and it protects players today |
| 3b | **A custom map downloaded on connect from a dedicated server** (then progress and resume) | unproven for dedicated servers (the client's own route is known for party joins only); an installed custom map can break the map list; the list holds 64 entries shared with the stock maps | TF6 measures first what the official client already does; CF3b builds what is missing |
| 4 | **Third person and a full-body animation on a player** | unproven; may be possible from server script alone | M1 decides; CF4 if the client must change |
| 5 | **Eight players in the stock scoreboard and portraits** | four rows; slots 5 to 8 raise an interface error every frame | CF5 |
| 6 | **Our own animations on enemies** | assets load from a zone like any other; playing them is a server-script matter through the actor kit, if the first probe (C2, E1) confirms it | none expected; if a client change proves necessary it becomes CF6 with the same rules |

Not client capabilities (the official client needs nothing new): server scripts (quest, Capsule Post, traps,
perks' logic, enemy rules), server-drawn HUD, weapons and camos (they ship in the map's own zone), the map's sounds, materials on stock
techniques.

## 2. Feature by feature

| Feature of the map | Needs | A player on today's official client gets | A player whose client has the capability gets |
|---|---|---|---|
| The map itself (19 zones) | 3a, 3b | Honest state: until TF6 shows the official client can receive a map from a dedicated server, or CF3 is in players' hands, a player on today's official client **cannot receive Station Zero by itself**. A manual install is not an acceptable fallback under the owner's rule that online content installs itself. **Recommendation to the owner**: keep the map on private test servers until one of the two is true; never place it where an unprepared client could be sent into a download that closes it | joins, downloads, plays |
| Quest, power, the Terminus, the Capsule Post, traps, activities | none | everything | the same |
| Six stock perks, four new perks | none for the effects; 1 for icons in the stock perk row | all ten perks work; the four new icons are drawn by the server beside the stock row | icons inside the stock row |
| Four wonder weapons, camos | none: they ship in the map's own zone, with the map (so 3a and 3b apply as for the map). Shipping them in the servers' global mod instead is a recommendation left to the owner: it changes the mod for every player of every map, and a failed mod download closes today's client | everything, on donor animation sets at first | the same |
| Seventy-eight zombies | 2 for real agents | **the hybrid crowd**: 78 bodies in the fight, each can be shot, killed for points and will attack; at most 24 are engine agents at a moment, the nearest ones (`07-ENEMIES.md` 2.2). This mode exists only if package E1's probes pass (hits on a script body above all); otherwise the official-client cap stays 24. In hybrid mode no zombie depends on agent records beyond 24; that every body is actually drawn is what proof 2 of `07-ENEMIES.md` 2.5 measures, nothing is assumed | 78 real agents on a server started with the capacity profile. Technically such a server can admit only clients with the capability and tells any other client so in one sentence at connect. Whether a public server ever runs that profile is the owner's decision |
| The Rollers and the Night Inspector | 6 (none expected) | our models and clips if the probe confirms the stock client plays them; otherwise the stock stand-ins with the same rules | the same |
| Server-drawn HUD (H1 to H9), STATION page, `.tab`, `.journal`, `.carried` | none | everything | the same |
| The full Tab screen, the journal reader, the network diagram | 1; 5 for eight rows | the server-drawn tier above; the stock four-row scoreboard on Tab | the three-page screen with eight rows |
| Emotes | 4 (to be decided by M1) | the emote if the stock client can play the clip, in first person for the emoter if third person is not available; otherwise `.e` answers "needs the updated client" and nothing else happens | third person, the full wheel |
| The emote wheel | 1 | the server-drawn wheel (`.e`, pointer by view direction) | the Lua ring |
| Eight players on the map | 5 | **Recommendation to the owner**: offer Station Zero with four slots to official clients until CF5 is in their hands, because slots 5 to 8 halve the frame rate on a stock client today (measured 2 Nov: 31 to about 15 frames per second) | eight slots |

## 3. Rules for the fork packages

1. One capability per branch, the smallest change that gives it, no project names or project-only behaviour in
   it, a test that runs without this project's servers, a short description of the kind the client project
   accepts (the project's `Aurora-PR-Rules` skill is the guide when the owner decides to propose one).
2. Every capability is negotiated: a server asks the client what it has; a missing capability selects the
   fallback or a clean refusal. A capability is never assumed.
3. The official client is part of every test: each CF package's proof includes the official client meeting
   the same server and getting the fallback with no error in its log.
4. Nothing is proposed, posted or released outside the project until the owner says so.
