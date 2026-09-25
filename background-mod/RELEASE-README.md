FULL THROTTLE BACKGROUND REMASTER
Version 0.1.0-beta.1 | Windows 64-bit | by Linn1024

INSTALL
1. Extract the entire downloaded ZIP to a folder. Keep Setup.exe and
   mod-payload.zip together. Do not run Setup.exe from inside the ZIP viewer.
2. Close Full Throttle Remastered and any background-switcher helper.
3. Run Setup.exe, click Browse, and select the GAME folder containing
   Throttle.exe and full.data. Click Install and wait for completion.
4. In your game folder, double-click
   "Play Full Throttle Background Remaster.cmd".

No separate Python, Frida, image tools or internet download is required.
Installation needs write access to the selected game folder and approximately
2 GB free space in addition to the extracted download. If Windows denies
access to a protected game directory, run Setup.exe as administrator.

PLAY
Custom graphics are selected initially. Use the game's remastered graphics
mode. F6 selects official remastered textures; F7 selects this mod's textures.
The game's original/classic graphics toggle remains available.
Keep the mod helper window open until the game closes. Starting Throttle.exe
normally plays without the live mod. Restart both game and helper after an
update. The helper operates only in the game process; it does not patch the
executable or full.data and does not edit saves.

REMOVE / UPDATE
Run Setup.exe from the extracted download, select the same game folder and
click "Remove installed mod". Then install a newer version if desired.
Alternatively, run FTBackgroundRemaster/FTBackgroundRemaster.exe and choose
Uninstall. When removing through the installed helper itself, Windows may
keep that running EXE; close it, then delete the remaining mod folder.
Changed or unrecognized files in the mod folder are preserved. Game files,
saves, other mods and the old development background-mod folder are untouched.

VERIFY / TROUBLESHOOT
Run FTBackgroundRemaster/FTBackgroundRemaster.exe and click Verify files.
If installation reports mismatched assets, verify/restore the original game
through your store client first. Legacy modifications to full.data are not
supported by this installer. Do not delete your saves.
If setup fails, read the message in its window; CLI failures are recorded in
setup-error.log under %LOCALAPPDATA%/FTBackgroundRemaster. The helper writes
session.log there in a per-install folder and displays its exact path.
Include the game build/store and log in reports. Removing a mod from a protected
game folder may also require running Setup.exe as administrator.
Do not run a second game instance while the mod helper is active.

COMPATIBILITY / BETA STATUS
Requires a separately installed Windows copy of Full Throttle Remastered.
Asset compatibility is checked during installation. Development used GOG build
Throttle-1.1.891868. Other builds/store editions are not gameplay-verified.
This is a beta: texture packing, installer operation and file integrity are
checked offline; complete scene/animation coverage still needs gameplay review.
This package has not been verified on a separate clean Windows PC.
It does not replace every character animation or cutscene. Visual issues may
remain in individual scenes or states.

CONTENTS / CREDITS
Includes detailed background artwork, selected scenery/interaction sprites,
cloud animation work and the F6/F7 live texture helper. Artwork uses AI-assisted
redraws with manual review, registration, color grading and sprite integration.
Original game art and Full Throttle belong to their respective owners. This is
an unofficial fan modification, not affiliated with the game developers.
Original texture payloads used by F6 are extracted from your own full.data at
installation; the game executable, archive, saves and standalone official
texture files are not included in the download.

Source: https://github.com/Linn1024/full-throttle-background-remaster
See THIRD-PARTY-NOTICES.txt and the installed licenses folder for dependencies.
