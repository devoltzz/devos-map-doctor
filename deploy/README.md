# Deploying the site

The site is static: everything runs in the visitor's browser. The host only serves files.

```
GitHub release vX  --(workflow "site")-->  site-vX.zip + .sha256 attached to the release
devo-sync  --(public API, every 15 min)-->  /opt/devo-site/www/releases/vX, then current -> releases/vX
devo-site (nginx)  <--  devo-tunnel (Cloudflare)  <--  visitors
```

## Once

1. Folders: `/opt/devo-site/www` (owned by uid 101, written by devo-sync) and `/opt/devo-site/data` (read only).
2. The game data pack: put `game_data.zip` in `/opt/devo-site/data`. It is made from an installed Warcraft III
   (`casc_wc3.py pacote`) and is never in git or in a release.
3. A Cloudflare tunnel with the public hostname of the site pointing at `http://devo-site:80`; its token in `.env`.
4. `docker compose up -d` in this folder (or the same file as a stack in your Docker manager).

## Each release

Publish the GitHub release; the `site` workflow attaches `site-<tag>.zip`. devo-sync puts it in place within 15
minutes (`docker logs devo-sync`). To go back: point `current` at an older folder in `releases/`.

## What the server keeps

Nothing about visitors: nginx has no access log, there are no cookies and no metrics. Every answer is
`Cache-Control: no-cache`, and the page keeps its own offline copy (`sw.js`).
