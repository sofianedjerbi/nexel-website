#!/bin/sh
# Build the playable demo into play/ from a CLEAN checkout of the game repo (only what is committed at REF).
#
#   tools/build_site.sh                       game repo: ~/megastructure, REF: HEAD
#   GAME=/path/to/megastructure REF=v0.3 tools/build_site.sh
#
# What it does:
#   1. clones the game repo (local clone, so nobody's uncommitted work gets in) and checks out REF
#   2. copies in the two things the game's build needs that git does not hold:
#        src/megastructure/web/audio/   the rendered sound effects and music (tools/build_audio.py output)
#        .cache/pyodide/                Python's library for the browser (else the build fetches it)
#   3. runs the game's own tools/build_pages.py (the same build tools/publish_demo.sh publishes) into play/
#   4. drops the build's README (the demo repo's), keeps the rest as built
#
# Every path the demo uses is relative, so play/ works under https://<user>.github.io/nexel-website/play/.
set -e
SITE=$(cd "$(dirname "$0")/.." && pwd)
GAME=${GAME:-$HOME/megastructure}
REF=${REF:-HEAD}
PYTHON=${PYTHON:-$GAME/.venv/bin/python}
WORK=$(mktemp -d "${TMPDIR:-/tmp}/nexel-site.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

SHA=$(git -C "$GAME" rev-parse --short "$REF")
echo "game: $GAME at $REF ($SHA)"
git clone -q --no-hardlinks "$GAME" "$WORK/game"
git -C "$WORK/game" checkout -q --detach "$SHA"

if [ -d "$GAME/src/megastructure/web/audio" ]; then
  mkdir -p "$WORK/game/src/megastructure/web/audio"
  cp -R "$GAME/src/megastructure/web/audio/." "$WORK/game/src/megastructure/web/audio/"
else
  echo "note: no built audio in $GAME (run its tools/build_audio.py first); the build will try to render it" >&2
fi
if [ -d "$GAME/.cache/pyodide" ]; then
  mkdir -p "$WORK/game/.cache"
  cp -R "$GAME/.cache/pyodide" "$WORK/game/.cache/pyodide"
fi

(cd "$WORK/game" && "$PYTHON" tools/build_pages.py "$WORK/play")
rm -f "$WORK/play/README.md"
[ -d "$SITE/play/brain" ] && mv "$SITE/play/brain" "$WORK/brain"     # (the brain view lives in play/ but is not the demo's)
rm -rf "$SITE/play"
mv "$WORK/play" "$SITE/play"
[ -d "$WORK/brain" ] && mv "$WORK/brain" "$SITE/play/brain"
echo "$SHA" > "$SITE/play/BUILD"
echo "built play/ from $SHA ($(du -sh "$SITE/play" | cut -f1))"
