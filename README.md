## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Vendor Dependencies](#vendor-dependencies)
5. [Installation & Build](#installation--build)
	* [Linux](#linux)
	* [macOS](#macos)
	* [Windows](#windows)
6. [Testing](#testing)
7. [Artifact Retrieval](#artifact-retrieval)
8. [Contributing](#contributing)
9. [License](#license)
10. [Contact](#contact)

---

## Project Overview

AravisWrapper is a Python/C extension that provides high-performance camera access via the Aravis library, wrapped into
an easy-to-install wheel package for Linux, macOS, and Windows . It uses cibuildwheel to automate multi-architecture
wheel builds and publishes artifacts for private repos via GitHub Actions .

## Features

* **Cross-platform builds:** Automated CI pipeline for x86\_64 and ARM64 on Linux, macOS, and Windows .
* **Vendor packaging:** Bundles Aravis shared libraries to eliminate external dependencies at runtime .
* **Artifact management:** Outputs wheels as GitHub Actions artifacts for easy download in private repositories .

## Prerequisites

* **Git** (≥2.0) – for source checkout.
* **Docker** (on Linux/macOS) – required for manylinux builds.
* **MSYS2** (on Windows) – to vendor Linux libraries under Windows.
* **Python** (3.10–3.12) – for build tooling.

## Vendor Dependencies

We vendor Aravis libraries inside `camera_reader/_vendor` so end users do not need system installs :

* Linux: `libaravis-0.8.so*`, `Aravis-0.8.typelib`
* macOS: `libaravis-0.8.dylib`, `Aravis-0.8.typelib`
* Windows: `libaravis-0.8-0.dll`, `Aravis-0.8.typelib`

## Installation & Build

Follow the steps below for your platform. All commands assume you are in the repository root.

### Linux

1. **Checkout & QEMU**

   ```bash
   git clone https://github.com/RhysEvan/AravisWrapper.git
   cd REPO
   ```
2. **Install Docker & QEMU helper**

   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io
   docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
   ```


3. **Build wheels**

   ```bash
   pip install cibuildwheel==2.23.3
   cibuildwheel . --output-dir wheelhouse
   ```
4. **Repair wheels**

   ```bash
   pip install auditwheel
   mkdir repaired
   for w in wheelhouse/*.whl; do auditwheel repair "$w" -w repaired/; done
   ```

### macOS

1. **Install Homebrew & dependencies**

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew install aravis pygobject3
   ```
2. **Build & delocate wheels**

   ```bash
   pip install cibuildwheel delocate-wheel
   cibuildwheel . --output-dir wheelhouse
   mkdir repaired
   delocate-wheel -w repaired wheelhouse/*.whl
   ```

### Windows

1. **Setup MSYS2**

* Download & install from [https://www.msys2.org](https://www.msys2.org)
* In MSYS2 Mingw64 shell:

  ```bash
  pacman -Sy --noconfirm mingw-w64-x86_64-aravis mingw-w64-x86_64-gobject-introspection
  ```

2. **Build wheels**

   ```bash
   pip install cibuildwheel
   cibuildwheel . --output-dir wheelhouse
   ```
3. **No repair needed** (DLLs are already vendored).

## Testing

After building, you can install and test locally:

```bash
pip install repaired/*.whl
python -c "import camera_reader; print(camera_reader.list_cameras())"
```

Ensure your camera is connected and discoverable.

## Artifact Retrieval

Since this repo is private, built wheels are available as **GitHub Actions artifacts** under each run’s **Artifacts**
tab . Download the `built-wheels` ZIP and extract the `.whl` files.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contact

For questions or support, open an issue or reach out to the maintainers at `<invilab@uantwerpen.be>`.
