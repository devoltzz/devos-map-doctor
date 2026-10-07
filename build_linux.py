# Builds the Linux binary in a Docker container (linux/Dockerfile), from Windows or Linux.
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
