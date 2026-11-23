# Contributing

## Commit messages: Conventional Commits

Every commit on main follows [Conventional Commits](https://www.conventionalcommits.org): CI checks each one
(`commitlint.config.mjs`: the conventional rules; body lines may be long).

    <type>(<scope>): <subject in lower case, no final full stop, about 72 characters at most>

    <body: what changed and why, as long as it needs>

- **type**: `feat` (a new page, post or demo feature), `fix`, `perf`, `refactor`, `docs`, `build`
  (a demo rebuilt from the game), `ci` (.github), `chore` (tools, anything else), `style`, `test`, `revert`.
- **scope**: `site` (landing page, css, img, fonts), `devlog`, `demo` (play/), `brain` (play/brain/), `tools`.

Optional hooks (ruff, and the message check at commit time): `uvx pre-commit install`.

## Publishing

GitHub Pages serves main as it is: a push to main is the release. There are no version tags here.
Before pushing, `python3 tools/make_site.py` (after editing `tools/landing.html` or a post) and
`python3 tools/check_links.py`; `.github/workflows/ci.yml` checks both on every pull request and push.
