#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Downloads and vendors the Aravis camera library for
# cross-platform compatibility. It detects the current OS and
# architecture, then downloads the appropriate Aravis libraries
# and GObject introspection files into the project's vendor directory.
#
# Supports: Linux (x86_64, arm64), macOS (Intel, Apple Silicon),
# and Windows (x86_64, arm64)
# ----------------------------------------------------------------------

set -e

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
  x86_64) ARCH_ID="x86_64" ;;
  amd64)  ARCH_ID="x86_64" ;;
  aarch64|arm64) ARCH_ID="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
esac

VENDOR_DIR="camera_reader/_vendor"
mkdir -p "$VENDOR_DIR"

if [[ "$OS" == "linux" ]]; then
  OUT_DIR="$VENDOR_DIR/linux_$ARCH_ID"
  mkdir -p "$OUT_DIR"
  PLATFORM_FLAG=""
  [[ "$ARCH_ID" == "x86_64" ]] && PLATFORM_FLAG="--platform linux/amd64"
  docker run --rm $PLATFORM_FLAG \
    -v "$(pwd)/$OUT_DIR":/vendor \
    ubuntu:22.04 bash -c "
      apt-get update && \
      apt-get install -y software-properties-common && \
      add-apt-repository universe && \
      apt-get update && \
      apt-get install -y libaravis-0.8-0 gir1.2-aravis-0.8 && \
      cp /usr/lib/${ARCH_ID}-linux-gnu/libaravis-0.8.so* /vendor/ && \
      cp /usr/lib/girepository-1.0/Aravis-0.8.typelib /vendor/
    "

elif [[ "$OS" == "darwin" ]]; then
  BREW_PREFIX=$(brew --prefix)
  if [[ "$ARCH_ID" == "x86_64" ]]; then
    OUT_DIR="$VENDOR_DIR/macosx_x86_64"
  else
    OUT_DIR="$VENDOR_DIR/macosx_arm64"
  fi
  mkdir -p "$OUT_DIR"
  brew install aravis pygobject3
  cp "$BREW_PREFIX/lib/libaravis-0.8.dylib"    "$OUT_DIR/"
  cp "$BREW_PREFIX/lib/girepository-1.0/Aravis-0.8.typelib" "$OUT_DIR/"

elif [[ "$OS" == "mingw"* || "$OS" == "msys" ]]; then
  if [[ "$ARCH_ID" == "x86_64" ]]; then
    MSYS_ENV="UCRT64"
    OUT_DIR="$VENDOR_DIR/win_amd64"
    PKG="mingw-w64-ucrt-x86_64-aravis"
  else
    MSYS_ENV="CLANG64"
    OUT_DIR="$VENDOR_DIR/win_arm64"
    PKG="mingw-w64-clang-aarch64-aravis"
  fi
  mkdir -p "$OUT_DIR"
  docker run --rm \
    -e MSYSTEM=$MSYS_ENV \
    -v "$(pwd)/$OUT_DIR":/vendor \
    ghcr.io/msys2/msys2-docker-experimental bash -lc "
      pacman --noconfirm -Syuu && \
      pacman --noconfirm -S $PKG && \
      cp /mingw64/bin/libaravis-0.8.dll /vendor/ && \
      cp /mingw64/lib/girepository-1.0/Aravis-0.8.typelib /vendor/
    "
else
  echo "Unsupported OS: $OS" >&2
  exit 1
fi

echo "Vendored Aravis files for $OS/$ARCH_ID in $OUT_DIR"
