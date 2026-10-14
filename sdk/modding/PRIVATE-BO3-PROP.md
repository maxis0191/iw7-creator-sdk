# Paquet privé du prop BO3 MP

Cette recette reprend le petit FF-B existant, sans conversion ni reconstruction.
Elle prépare un projet pour le `Creator.ps1` existant. Les archives restent
privées et locales ; les assets, dumps et exécutables ne vont pas dans Git.

Le contrat retenu identifie `p7_fre_platform_cap_02`, zone donneuse
`mp_freerun_04`, affiché sur Spaceland (`cp_zmb`). Il déclare cinq surfaces,
560 sommets et 490 triangles.
Les cinq slots utilisent le matériau IW7
`mopw/character_park_clown_zombie_shoes`. Les textures BO3, la collision, les
animations, l'IA, les armes, les maps Zombies et l'acceptation propriétaire
restent non qualifiées.

La session agent du 14 octobre 2026 a observé le prop : processus original
PTY69654 terminé avec code 0, acteur 772, 21 poses, suppression à zéro, restauration
et lease libérée. Les contrôleurs historiques `PixelsVerified` et
`RenderedGeometryVerified` restent `false` ; l'observation visuelle est une pièce
distincte. Cette recette ne rejoue pas la session. L'installation et la reconnexion
depuis le nouveau ZIP restent à vérifier séparément.

## Prérequis natif fourni séparément

Le client et le serveur privés doivent employer le candidat déjà qualifié :

| Identité | Valeur |
| --- | --- |
| Upstream | `77e6d4d24e918ee363b3feee3735c3b889dff7d7` |
| Overlay privé | `caccd6981578d96aee44a288108b80956053be48` |
| Exécutable Native958 | 6 097 920 octets, SHA-256 `958613f3ade0347f991071a0a8a8502cfb66c816c5c084c5214f05078f7b0296` |
| Build manifest | SHA-256 `969f4af7b49826fdaca9c83774d39849bf0446adb311049bdc81e34a371145a8` |
| Protocole de la session | `2` |

Le champ historique `Protocol: 1` du build manifest reste conservé. Le protocole
2 vient de la session réelle. Le pin upstream du contrat SDK est une assertion
d'environnement ; il n'identifie pas à lui seul l'overlay ni l'exécutable. La
recette enregistre leurs identités attendues, sans lire ni distribuer le binaire.
Un client upstream seul n'est pas qualifié pour cette scène.

## Préparer le projet puis les deux archives

Employer un workspace source composé depuis la révision SDK revue et des sorties
neuves. Donner explicitement les entrées retenues ; aucun chemin de machine n'est
déduit. La lecture du FF réel et les ZIP utilisent le créneau Analysis coordonné
avec le chat principal.

```powershell
python -B ./sdk/modding/prepare_private_bo3.py `
  --fastfile $ExistingFF --server-script $ReviewedServerScript `
  --readback $RetainedReadback --reference-root $RetainedReferenceRoot `
  --output $FreshProject

$upstream = '77e6d4d24e918ee363b3feee3735c3b889dff7d7'
./sdk/modding/Creator.ps1 -Project $FreshProject -Action Plan -Target native `
  -ClientSource $upstream -ServerSource $upstream -Protocol 2 -Json

./sdk/modding/Creator.ps1 -Project $FreshProject -Action Package -Target native `
  -ClientSource $upstream -ServerSource $upstream -Protocol 2 `
  -Output $FreshCreatorZip -Json

./sdk/modding/Creator.ps1 -Project $FreshProject -Action Package -Target native `
  -ClientSource $upstream -ServerSource $upstream -Protocol 2 `
  -PackageLayout player -PlayerLanguage fr -Output $FreshPlayerZip -Json
```

Le FF doit faire 9 904 octets, SHA-256
`50ca9124d35f4ea5e9f017adafcf012df01b9991d1fcde2597c8f0f58aabcd0c`.
Le script serveur doit faire 8 607 octets, SHA-256
`a8b8d07e7d3bad415b1bb69d09954b21342ba54c9d4b4d7137321f9e3f8e637a`.
Le reader retenu doit faire 2 274 octets, SHA-256
`7f8b628fd3dd8250c24c959017be139b81f6aad92ebe5e1e885d42c98dd6351f`.
Les trois petits textes de référence sont contrôlés aux chemins relatifs fixes
`zone_source/paris_model_probe_recipient.csv`, `zone_source/paris_model_probe.csv`
et `netconststrings/ncs_mdl_paris_model_probe.json`.

`project-evidence.json` décrit la représentation de chaque nœud. La fermeture
`complete` est celle de l'inventaire déclaré du transport. Les hashes des dumps
model/surface sont les déclarations du reader retenu ; ils ne sont pas remesurés.
Le hash du matériau représente le CSV de référence, celui du rawfile le CSV de
zone, et celui du NCS son texte producteur. Ils ne prouvent pas les octets retail
du matériau, sa fermeture techset/images, ni la sérialisation du rawfile/NCS.
Seuls le FF et le GSC livrés sont remesurés comme payloads. L'ancien état `Failed`
du build et toutes les pièces originales restent intacts.

L'archive créateur existante contient le manifeste et les chemins de staging
`server/` et `fastdl/`. Elle n'est pas un lanceur serveur. Le receipt de projet
reste à côté pour la revue des représentations. Le ZIP joueur contient seulement
`PLAY.txt` et `mods/paris_bo3_static_probe/mod.ff`. Il exclut scripts serveur,
PowerShell, code source, outils, executable natif et PDB.

La recette reste autonome : aucune dépendance ni déclaration de conflit à
résoudre par le stager. Les contrôles Distribution d'un seul `fs_game` et des
collisions de noms d'assets restent applicables à tout autre projet actif.

## Installation joueur et retour arrière

1. Fermer le jeu. Si `mods/paris_bo3_static_probe` existe déjà, déplacer ce dossier
   entier vers une sauvegarde hors du dossier du jeu.
2. Copier le dossier `mods` du ZIP joueur dans le jeu existant. Conserver le stock
   du jeu ; aucun clone n'est nécessaire.
3. Lancer le client Native958 fourni séparément et rejoindre la session privée
   coordonnée par l'opérateur. Le serveur de la preuve a été fermé ; aucune
   disponibilité actuelle, adresse publique ou commande de connexion n'est promise.
4. Pour annuler, fermer le jeu, retirer uniquement le dossier
   `mods/paris_bo3_static_probe` installé, puis remettre la sauvegarde entière.
   Ne pas fusionner les dossiers.

Le serveur utilise la vraie fixture, avec ses gardes dedicated, lab/protection,
un joueur, `cp_zmb`, `fs_game=mods/paris_bo3_static_probe` et port de test 27116.
Son activation, ses sauvegardes et sa restauration appartiennent aux helpers
opérateur déjà revus. Main UDP27016 et les banques ne sont pas touchés par la
recette. Les messages dans le jeu restent en anglais.

`packaged` ou un résultat statique `ready` indique l'intégrité et le contrat du
paquet. `ready_to_deploy`, `runtime_ready` et `owner_accepted` restent faux.
