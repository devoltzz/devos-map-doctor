"""build_linux.py - the Linux build of the program: dist/DevosMapDoctor-linux-x86_64, one file, in a Docker container
(linux/Dockerfile: Ubuntu 22.04, so it runs on glibc 2.35 and newer). Works from Windows (Docker Desktop) and Linux.

    python build_linux.py

Inside the container: pjass from its source (github.com/lep/pjass, the commit the site uses) for Linux, then build.py,
which on Linux builds mpqcrypt.so and leaves the system's libraries (GTK, WebKitGTK, glib...) out of the program.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGE = 'devos-map-doctor-linux'
PJASS_COMMIT = '378a1ca'
OUT = 'DevosMapDoctor-linux-x86_64'

STEPS = '''set -e
git clone -q https://github.com/lep/pjass.git /tmp/pjass
git -C /tmp/pjass checkout -q {commit}
python web/build_pjass.py --src=/tmp/pjass --out=/tmp/pjass-out --native
PJASS=/tmp/pjass-out/pjass python build.py
cp dist/DevosMapDoctor dist/{out}
chmod 755 dist/{out}
if [ -n "$HOST_UID" ]; then chown -R "$HOST_UID:$HOST_GID" dist build doctor/mpq; fi
'''


def main():
    subprocess.run(['docker', 'build', '-q', '-t', IMAGE, os.path.join(ROOT, 'linux')], check=True)
    env = []
    if hasattr(os, 'getuid'):
        env = ['-e', 'HOST_UID=%d' % os.getuid(), '-e', 'HOST_GID=%d' % os.getgid()]
    steps = STEPS.format(commit=PJASS_COMMIT, out=OUT)
    r = subprocess.run(['docker', 'run', '--rm', '-v', ROOT + ':/src', '-w', '/src'] + env +
                       [IMAGE, 'bash', '-c', steps])
    if r.returncode:
        return r.returncode
    print('built', os.path.join(ROOT, 'dist', OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
