# VirtualBrowser Chromium Builder
# This Dockerfile builds a fingerprint-modified Chromium browser
# Based on Ungoogled Chromium

FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    python3 \
    python3-pip \
    curl \
    wget \
    lsb-release \
    sudo \
    pkg-config \
    libglib2.0-dev \
    libnss3-dev \
    libxss-dev \
    libappindicator3-dev \
    libindicator3-dev \
    libasound2-dev \
    libatk-bridge2.0-dev \
    libatk1.0-dev \
    libcairo2-dev \
    libcups2-dev \
    libdbus-1-dev \
    libdrm-dev \
    libgbm-dev \
    libgtk-3-dev \
    libnspr4-dev \
    libpango1.0-dev \
    libx11-xcb-dev \
    libxcb-dri3-dev \
    libxcomposite-dev \
    libxcursor-dev \
    libxdamage-dev \
    libxfixes-dev \
    libxi-dev \
    libxrandr-dev \
    libxshmfence-dev \
    libxtst-dev \
    ninja-build \
    clang \
    && rm -rf /var/lib/apt/lists/*

# Install depot_tools
RUN git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git /opt/depot_tools
ENV PATH="/opt/depot_tools:${PATH}"

# Create build user
RUN useradd -m -s /bin/bash builder && echo "builder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /home/builder

# Copy build scripts
COPY build.sh /home/builder/build.sh
COPY patches/ /home/builder/patches/

RUN chown -R builder:builder /home/builder

USER builder

# Build script will be run with volume mounts
ENTRYPOINT ["/home/builder/build.sh"]
