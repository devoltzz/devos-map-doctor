# The Linux build: Ubuntu 22.04 (glibc 2.35), Python 3.14, zlib-ng (build_linux.py runs it).
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -q \
 && apt-get install -y -q --no-install-recommends software-properties-common gpg-agent \
 && add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update -q \
 && apt-get install -y -q --no-install-recommends python3.14 python3.14-dev python3.14-venv build-essential pkg-config \
    libgirepository1.0-dev libcairo2-dev gir1.2-gtk-3.0 gir1.2-webkit2-4.1 flex bison git binutils ca-certificates \
    cmake curl \
 && rm -rf /var/lib/apt/lists/*
RUN curl -sL https://github.com/zlib-ng/zlib-ng/archive/refs/tags/2.2.4.tar.gz | tar xz -C /tmp \
 && cmake -S /tmp/zlib-ng-2.2.4 -B /tmp/zng -DZLIB_COMPAT=ON -DZLIB_ENABLE_TESTS=OFF -DWITH_GTEST=OFF \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local >/dev/null \
 && cmake --build /tmp/zng -j >/dev/null && cmake --install /tmp/zng >/dev/null && ldconfig \
 && rm -rf /tmp/zlib-ng-2.2.4 /tmp/zng
RUN python3.14 -m venv /venv \
 && /venv/bin/pip install -q --upgrade pip \
 && /venv/bin/pip install -q "numpy>=1.24" "pillow>=10.0" "pywebview>=6.2" "pyinstaller>=6.0" "PyGObject<3.51" \
    pycairo ziglang==0.16.0 zopfli==0.4.3 lupa==2.8 ctranslate2==4.8.2 sentencepiece==0.2.2
ENV PATH=/venv/bin:$PATH
