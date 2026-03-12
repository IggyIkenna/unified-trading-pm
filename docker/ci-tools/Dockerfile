# CI Tools Builder Image
#
# PURPOSE: Cloud Build step executor with all CI tools pre-installed.
# Used as the `name:` field in cloudbuild.yaml steps to replace per-step
# `apt-get install ripgrep` across all ~51 Python repos.
#
# BASE IMAGE NOTE: This is CI *infrastructure*, not a trading service. It does NOT
# use the unified-trading-library base image (that would create a circular dependency —
# this image is used to BUILD that image). Standard ubuntu:22.04 is intentional here.
#
# USAGE in cloudbuild.yaml:
#   - name: 'asia-northeast1-docker.pkg.dev/$PROJECT_ID/unified-trading-pm/ci-tools:latest'
#     entrypoint: bash
#     args: ['-c', 'bash scripts/quality-gates.sh --no-fix']
#
# TOOL VERSIONS (update ARGs below + rebuild to bump):
#   ripgrep:    14.1.1
#   shellcheck: v0.10.0
#   python:     3.13.9
#   uv:         latest at build time (pinned via requirements)
#   jq:         system (ubuntu 22.04 ships 1.6+)

FROM ubuntu:22.04

ARG RG_VERSION=14.1.1
ARG SC_VERSION=v0.10.0
ARG PYTHON_VERSION=3.13.9
ARG DEBIAN_FRONTEND=noninteractive

# System packages: python build deps, jq, curl, git, ca-certs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    jq \
    make \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
  && rm -rf /var/lib/apt/lists/*

# ripgrep — pinned musl binary (no libc dependency, portable)
RUN curl -fsSL \
    "https://github.com/BurntSushi/ripgrep/releases/download/${RG_VERSION}/ripgrep-${RG_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
    | tar -xz --strip-components=1 -C /usr/local/bin \
        "ripgrep-${RG_VERSION}-x86_64-unknown-linux-musl/rg" \
  && chmod +x /usr/local/bin/rg \
  && rg --version

# shellcheck — pinned binary
RUN curl -fsSL \
    "https://github.com/koalaman/shellcheck/releases/download/${SC_VERSION}/shellcheck-${SC_VERSION}.linux.x86_64.tar.xz" \
    | tar -xJ --strip-components=1 -C /usr/local/bin \
        "shellcheck-${SC_VERSION}/shellcheck" \
  && chmod +x /usr/local/bin/shellcheck \
  && shellcheck --version

# Python 3.13.9 via pyenv (ubuntu 22.04 ships 3.10 — we need exact version)
ENV PYENV_ROOT=/opt/pyenv
ENV PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:${PATH}"
RUN curl -fsSL https://pyenv.run | bash \
  && pyenv install ${PYTHON_VERSION} \
  && pyenv global ${PYTHON_VERSION} \
  && python --version

# uv — copy binary from official image (avoids pip bootstrap chicken-and-egg)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN uv --version

# Node.js 20 (for agent workflows that need claude-code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && node --version \
  && npm --version

# Verify all tools are on PATH
RUN rg --version && shellcheck --version && python --version && uv --version && node --version

LABEL org.opencontainers.image.title="unified-trading-pm/ci-tools" \
      org.opencontainers.image.description="CI builder image with ripgrep, shellcheck, Python 3.13.9, uv, Node 20" \
      rg.version="${RG_VERSION}" \
      shellcheck.version="${SC_VERSION}" \
      python.version="${PYTHON_VERSION}"
