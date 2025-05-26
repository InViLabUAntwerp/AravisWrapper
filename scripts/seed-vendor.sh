#!/usr/bin/env bash
set -e
command -v docker >/dev/null 2>&1 || { echo "Docker is required"; exit 1; }
command -v brew   >/dev/null 2>&1 || echo "Homebrew recommended on macOS"

VEND=./camera_reader/_vendor
mkdir -p "$VEND"

for ARCH in x86_64 arm64; do
  OUT="$VEND/linux_${ARCH}"
  mkdir -p "$OUT"

  FLAG=""
  [[ "$ARCH" == "x86_64" ]] && FLAG="--platform linux/amd64"
  [[ "$ARCH" == "arm64"  ]] && FLAG="--platform linux/arm64"

  docker run --rm $FLAG \
    -v "$(pwd)/$OUT":/vendor ubuntu:22.04 bash -c "
      set -e
      apt-get update && \
      apt-get install -y libaravis-0.8-0 gir1.2-aravis-0.8 dpkg-dev && \
      MULTIARCH=\$(dpkg-architecture -qDEB_HOST_MULTIARCH) && \
      cp /usr/lib/\${MULTIARCH}/libaravis-0.8.so* /vendor/ && \
      cp /usr/lib/\${MULTIARCH}/girepository-1.0/Aravis-0.8.typelib /vendor/
    "
  echo "→ Vendored Linux/$ARCH"
done

for ARCH in x86_64 arm64; do
  OUT="$VEND/macosx_${ARCH}"
  mkdir -p "$OUT"
  brew install aravis pygobject3 || true
  HB=$(brew --prefix)
  cp "$HB/lib/libaravis-0.8.dylib"             "$OUT/" || echo "lib missing"
  cp "$HB/lib/girepository-1.0/Aravis-0.8.typelib" "$OUT/" || echo "typelib missing"
  echo "→ Vendored macOS/$ARCH"
done

for ENV in UCRT64 CLANG64; do
  if [[ "$ENV" == "UCRT64" ]]; then
    PKG="mingw-w64-ucrt-x86_64-aravis"; OUT="$VEND/win_amd64"
  else
    PKG="mingw-w64-clang-aarch64-aravis"; OUT="$VEND/win_arm64"
  fi
  mkdir -p "$OUT"
  docker run --rm -e MSYSTEM=$ENV -v "$(pwd)/$OUT":/vendor \
    ghcr.io/msys2/msys2-docker-experimental bash -lc "
      pacman --noconfirm -Syuu && pacman --noconfirm -S $PKG && \
      cp /mingw64/bin/libaravis-0.8.dll /vendor/ && \
      cp /mingw64/lib/girepository-1.0/Aravis-0.8.typelib /vendor/
    "
  echo "→ Vendored Windows/${OUT##*/}"
done

echo "All platforms vendored under $VEND"
