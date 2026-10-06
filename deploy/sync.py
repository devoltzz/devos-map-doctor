"""sync.py - devo-sync: keeps devo-site on the latest release of the program. Every INTERVAL seconds it asks GitHub's
public API for the latest release of REPOSITORY, and when the release has a site zip (site-<tag>.zip and its .sha256,
attached by the `site` workflow) that is not the one served, it downloads both, checks the sha256, unpacks the zip
into WWW/releases/<tag> and points WWW/current at it in one step (the old site serves until then; the last KEEP
releases stay, for going back by hand). Standard library only; no token: the API is public and asked 4 times an hour.

Environment: REPOSITORY (owner/name), WWW (/srv/www), INTERVAL (900), KEEP (3), API (https://api.github.com).
  python sync.py [--once]
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile

REPOSITORY = os.environ.get('REPOSITORY', 'devoltzz/devos-map-doctor')
WWW = os.environ.get('WWW', '/srv/www')
INTERVAL = int(os.environ.get('INTERVAL', '900'))
KEEP = int(os.environ.get('KEEP', '3'))
API = os.environ.get('API', 'https://api.github.com').rstrip('/')
AGENT = 'devo-sync'


def log(text):
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + text, flush=True)


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'application/vnd.github+json'
                                               if not binary else 'application/octet-stream'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def served():
    """The tag WWW/current points at, or None."""
    link = os.path.join(WWW, 'current')
    return os.path.basename(os.readlink(link)) if os.path.islink(link) else None


def safe_extract(zip_path, target):
    """The zip into `target`, refusing a member that would land outside it."""
    root = os.path.realpath(target)
    with zipfile.ZipFile(zip_path) as z:
        for m in z.infolist():
            dest = os.path.realpath(os.path.join(target, m.filename))
            if dest != root and not dest.startswith(root + os.sep):
                raise ValueError('zip member outside the folder: %r' % m.filename)
        z.extractall(target)


def switch(tag):
    """WWW/current -> releases/<tag>, replaced in one rename (never a moment without a site)."""
    tmp = os.path.join(WWW, '.current.new')
    if os.path.lexists(tmp):
        os.remove(tmp)
    os.symlink(os.path.join('releases', tag), tmp)
    os.replace(tmp, os.path.join(WWW, 'current'))


def prune(keep_tag):
    base = os.path.join(WWW, 'releases')
    olds = sorted((os.path.getmtime(os.path.join(base, d)), d) for d in os.listdir(base) if d != keep_tag)
    for _t, d in olds[:max(0, len(olds) - (KEEP - 1))]:
        shutil.rmtree(os.path.join(base, d), ignore_errors=True)
        log('removed the old site %s' % d)


def once():
    """-> the tag served after this check."""
    rel = json.loads(get('%s/repos/%s/releases/latest' % (API, REPOSITORY)))
    tag = rel['tag_name']
    if served() == tag:
        return tag
    assets = dict((a['name'], a['browser_download_url']) for a in rel.get('assets', []))
    name = 'site-%s.zip' % tag
    if name not in assets or name + '.sha256' not in assets:
        log('release %s has no %s yet' % (tag, name))
        return served()
    expected = get(assets[name + '.sha256'], binary=True).decode('ascii', 'replace').split()[0].lower()
    os.makedirs(os.path.join(WWW, 'releases'), exist_ok=True)
    work = tempfile.mkdtemp(prefix='.sync-', dir=WWW)
    try:
        zip_path = os.path.join(work, name)
        h = hashlib.sha256()
        req = urllib.request.Request(assets[name], headers={'User-Agent': AGENT, 'Accept': 'application/octet-stream'})
        with urllib.request.urlopen(req, timeout=600) as r, open(zip_path, 'wb') as f:
            for block in iter(lambda: r.read(1 << 20), b''):
                h.update(block)
                f.write(block)
        if h.hexdigest() != expected:
            raise ValueError('%s: sha256 %s, the release says %s' % (name, h.hexdigest(), expected))
        unpacked = os.path.join(work, 'site')
        safe_extract(zip_path, unpacked)
        if not os.path.isfile(os.path.join(unpacked, 'index.html')):
            raise ValueError('%s has no index.html' % name)
        dest = os.path.join(WWW, 'releases', tag)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.rename(unpacked, dest)
        switch(tag)
        log('serving %s (sha256 %s)' % (tag, expected[:12]))
        prune(tag)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return tag


def main(argv):
    log('devo-sync: %s every %d s into %s' % (REPOSITORY, INTERVAL, WWW))
    while True:
        try:
            once()
        except Exception as e:  # noqa: BLE001 -- the next check tries again; the site already served keeps serving
            log('check failed: %s: %s' % (type(e).__name__, e))
        if '--once' in argv:
            return 0
        time.sleep(INTERVAL)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
