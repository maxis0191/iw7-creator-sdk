# Soul Box demo

An original BO3-inspired Zombies mechanic using the IW7 retail
`zmb_coin_alien` token. It includes no BO3 model, texture, sound or game data.
Kill six ordinary zombies within 384 engine units of the token, then use it to
refill the equipped firearm's magazine and reserve ammunition. The team can
claim exactly one reward per map. The HUD and token change with progress.

The real `generic_zombie` killed callback supplies the credited player, weapon
and means of death. The observer snapshots actor classification and death origin
before forwarding all nine arguments to the original callback exactly once;
only then does it credit progress. The player notification arrives after actor
fields are unavailable and cannot safely classify the dead actor. Only
unreserved axis `generic_zombie` deaths count; suicides and poor-death cleanup do
not. The script preserves stock waves, death counters, loot and banks.
Players joining later receive current team progress. Respawns rebuild their HUD
without another death observer. Disconnect and game end remove HUDs; map end
deletes the token and restores the callback if this observer still owns it.

For an existing **private test dedicated**, install the editable script at
`iw7-mod/custom_scripts/cp/sdk_soulbox_demo_v1.gsc`. Enable
`sdk_soulbox_demo_enable 1`, use Spaceland (`cp_zmb`), a nonempty password,
`sv_lanOnly 1` and `sv_cheats 0`, and keep UDP27016 for Main. The first playable
spawn places the shared token 96 units in front of the player. Ordinary clients
need no download. A native test build must also suppress master heartbeat;
password and script guards alone are not browser privacy evidence.

The server-owned `Agent-Lab.ps1 -ObservationMode soulbox` provides a separate,
protected single-client demonstration. Its fixture uses diagnostic aim and real
native firing/Use inputs. It does not deal scripted damage or fabricate kills.
That fixture is excluded from the creator payload. Protection, snapshots,
captures and restoration belong to the test harness, not this gameplay script.

Protected native-input runs F/G/H credited six natural nearby bullet kills and
rendered the 6/6 HUD. G's two 350 ms Use inputs did not reach the token listener;
its visible stock ammo pickup was not a Soul Box reward. H's explicit retail
Use range/FOV (120/360) reached an
actual token trigger after two engine button edges. Reserve and magazine refill
operations returned, then gameplay ended before the final reward receipt.
The run remains failed; its owned empty frontend was recovered and all files,
Main audit and resource ownership restored.

H also reported a script error: usetriggerrequirelookat refuses script_model;
retail applies that method to interaction_trigger. I removes the invalid call
and retains the range/FOV. The next source keeps the ready token's observed
green state and adds ammunition
readback evidence. It removes the unqualified cosmetic `fx/blue` transition;
retail selects blue for `zmb_coin_space`, while this example uses
`zmb_coin_alien`. That transition is a suspect, not a proven cause of the ended
session. The completion HUD distinguishes a claimed reward. Actual
I confirmed clip12/12 and reserve120/120 after genuine Use, then ended before
the final completion hint change returned. J removes only that late hint update
and retains the earlier hint plus completion HUD/message/notify. The exact hint
constraint remains unproven. J passed a fresh protected private run: six natural
bullet kills filled the token; actual Use refilled the equipped Kendall reserve
from 20 to 120 with magazine 12/12. All completion operations returned, one
REWARD was recorded, and a newly accepted Use after release kept rewards at one.
A real native frame shows 6/6 and "Completed | Ammunition reward claimed".
The original host closed/restored managed files and Main audit, preserved bank
state and released ownership. No post-refill depletion test was added.

The retained "Collect ammunition reward" hint remains visible after claiming;
that is a known UX limitation of this mitigation. The HUD supplies the completed
state. This refills the equipped firearm only, not the complete retail Max Ammo
powerup callback. Multiplayer, recipient closure and owner acceptance remain
pending.

The template manifest records stock-model closure as pending. Parse/compile
success does not prove runtime linking, rendering, multiplayer, recipient
closure or owner acceptance. Current results are in the dated validation file;
do not describe this mechanic as a BO3 asset port.

Rollback: stop the exact empty test dedicated through its ordinary guard,
restore any previously installed script from its dated backup (or remove only
the newly installed script), and remove the opt-in configuration. The laboratory
runner restores its own candidate/client files and verifies their hashes.
