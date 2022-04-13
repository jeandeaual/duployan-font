# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.231.5/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon): 3, 3.10, 3.9, 3.8, 3.7, 3.6, 3-bullseye, 3.10-bullseye, 3.9-bullseye, 3.8-bullseye, 3.7-bullseye, 3.6-bullseye, 3-buster, 3.10-buster, 3.9-buster, 3.8-buster, 3.7-buster, 3.6-buster
ARG VARIANT="3.9"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

ARG VARIANT
ARG FONTFORGE_COMMIT="aa062f4cbd1db21e27b2620f16993ebe4c540ab6"
ARG HARFBUZZ_VERSION="4.1.0"

# Install additional OS packages.
# hadolint ignore=DL3008
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    packaging-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Install FontForge
RUN curl -Lo fontforge.zip "https://github.com/fontforge/fontforge/archive/${FONTFORGE_COMMIT}.zip" \
    && unzip fontforge.zip \
    && mv "fontforge-${FONTFORGE_COMMIT}" fontforge \
    && rm fontforge.zip

WORKDIR /opt/fontforge

RUN curl -O https://patch-diff.githubusercontent.com/raw/fontforge/fontforge/pull/4232.patch \
    && patch -p1 <4232.patch \
    && rm 4232.patch

WORKDIR /opt/fontforge/build

RUN cmake -G Ninja \
    -D CMAKE_INSTALL_PREFIX="/opt/fontforge/build/target" \
    -D ENABLE_DOCS=OFF \
    -D ENABLE_GUI=OFF \
    -D ENABLE_LIBGIF=OFF \
    -D ENABLE_LIBJPEG=OFF \
    -D ENABLE_LIBPNG=OFF \
    -D ENABLE_LIBREADLINE=OFF \
    -D ENABLE_LIBSPIRO=OFF \
    -D ENABLE_LIBTIFF=OFF \
    -D ENABLE_LIBUNINAMESLIST=OFF \
    -D ENABLE_PYTHON_EXTENSION=ON \
    -D ENABLE_NATIVE_SCRIPTING=OFF \
    -D ENABLE_WOFF2=OFF \
    .. \
    && ninja \
    && ninja install

# Add site-packages to the default search path
ENV PYTHONPATH="/opt/fontforge/build/target/lib/python${VARIANT}/site-packages${PYTHONPATH:+:}${PYTHONPATH}"

WORKDIR /opt

# Install HarfBuzz
COPY Makefile /opt
RUN make HB_VERSION="${HARFBUZZ_VERSION}" hb-shape \
    && rm Makefile

# Add HarfBuzz to path
ENV PATH="/opt/.hb/harfbuzz-${HARFBUZZ_VERSION}/util${PATH:+:}${PATH}"

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
COPY dev-requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/dev-requirements.txt \
   && rm -rf /tmp/pip-tmp
