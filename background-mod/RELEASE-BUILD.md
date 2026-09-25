# Public Windows beta package

`release_app.py` is a separate player-facing installer/launcher. It reads a
prebuilt, relative-path catalog and requires only bundled Frida and Python/Tk.
It never imports the development image toolchain or rebuilds textures at launch.

Version: `0.1.0-beta.1`. Prepared from the v27 artwork: 594 texture pairs across
106 distinct room identifiers, plus cloud frame payloads. The public ZIP ships
only custom texture data, helper/runtime, notices and documentation. Official
texture payloads are extracted from the player's own archive at installation
and checked against expected SHA-256 values. Legacy archive modifications are
rejected; the user must restore the original game archive first.

## Build

Use Windows x64, Python 3.12.10, Frida 17.18.0, PyInstaller 6.22.3 and hooks
2026.7. A complete local art workspace and freshly prepared
`live-switcher/textures.json` are required. This source repository alone does
not include the artwork or original game assets.

1. Run `build_release.py` (copies local dependency licenses; downloads Tcl's
   license from its official source repository only if absent locally).
2. Run `python -m PyInstaller --noconfirm --onefile --windowed --name Setup
   --distpath release/0.1.0-beta.1 --workpath release/build --specpath release
   release_app.py` as one command.
3. Run `test_release.py`, then `test_release.py --integration`.
4. Run `finalize_release.py` to produce the allowlisted upload ZIP and SHA-256.

The integration test builds a temporary archive fixture from locally extracted
originals, copies the game executable solely as a presence fixture, and tests
the actual frozen installer. It never launches the game. It verifies all
texture/cloud hashes, relocation, uninstall, unchanged game files, and keeping
a user-added file. The frozen runtime self-test initializes hidden Tk and
enumerates processes through Frida. This is not a separate-PC or gameplay test.

## Installation behavior

Installation stages and validates files before committing a new
`FTBackgroundRemaster` subdirectory and a dedicated launch CMD. Game files and
saves remain untouched. Failures remove only the newly created staging folder.
Existing installations must be uninstalled before updating. Removal checks an
ownership manifest and keeps modified/unrecognized files; removal through the
external Setup executable also removes the installed launcher. A running
installed launcher can remain due to Windows file locking, as explained in the
player README. Path traversal and rollback behavior have unit coverage.
Runtime logs are stored under LocalAppData, so play does not require writing
to a protected game installation directory.

## Publication

Upload `release/Full-Throttle-Background-Remaster-0.1.0-beta.1-Windows.zip`.
Use `MODDB-DESCRIPTION.md` as listing text and classify this as a Windows beta.
Read the player README and retain the SHA-256 beside your release. The package
has not been uploaded or published by the build scripts.
