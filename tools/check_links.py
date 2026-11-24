"""Check that every local link in the site's pages points at a file that is there.

    python3 tools/check_links.py            # exit 1 and a list when a link is broken
    python3 tools/check_links.py _site      # the site as deployed (pages.yml): the game in play/ too

Reads href= and src= in every .html page (the demo under play/ too; not the templates in tools/). Links to other sites, mail,
page anchors and data: URLs are not checked (CI has no business fetching the web on every push).
A link to a folder needs its index.html. Plain Python, no packages.
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
GAME = ROOT / "play"                 # the game's build: placed there at deploy (pages.yml), not committed; play/brain/ is ours
ATTR = re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
SKIP_DIRS = {".git", "node_modules", ".preview", "shots", "tools"}  # tools/landing.html is a template


def local_target(page: Path, link: str) -> Path | None:
    link = link.strip()
    if not link or link.startswith(("#", "data:", "mailto:", "javascript:", "tel:", "blob:")) or "${" in link or "{{" in link:
        return None
    parts = urlsplit(link)
    if parts.scheme or parts.netloc:
        return None
    path = unquote(parts.path)
    if not path:
        return None
    target = (ROOT / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def main() -> int:
    broken = []
    pages = [p for p in ROOT.rglob("*.html") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)]
    for page in sorted(pages):
        for m in ATTR.finditer(page.read_text(encoding="utf-8", errors="replace")):
            target = local_target(page, m.group(1) if m.group(1) is not None else m.group(2))
            if target is not None and not (GAME / "index.html").exists() and target.is_relative_to(GAME) and not target.is_relative_to(GAME / "brain"):
                continue                                         # (a checkout without the game: its links are checked at deploy)
            if target is not None and not target.exists():
                broken.append(f"{page.relative_to(ROOT)}: {m.group(1) or m.group(2)}")
    print(f"{len(pages)} pages checked, {len(broken)} broken links")
    for b in broken:
        print("  " + b)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
