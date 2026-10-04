# ProdCast Manager 0.6

Windows application for installing and updating ProdCast through SSH.

This directory contains the source, tests, resources, and Windows build definition for the standalone ProdCast Manager executable.

## Documentation

- [Русский](README-RU.md)
- [English](README-EN.md)
- [Offline installation](OFFLINE-EN.md)
- [Изменения 0.5](CHANGES-0.5-RU.md)

## Build on Windows

Use Python 3.11 with Tcl/Tk installed. From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.lock.txt
.\build.ps1 -Python .\.venv\Scripts\python.exe
```

The build script runs tests, builds single-file GUI and CLI executables, and checks packaged resources and GUI initialization. Output is written to `dist/`.

To run from source:

```powershell
.\.venv\Scripts\python.exe manager.py
```

Local profiles, credentials, caches and logs are not part of this source snapshot. Keep virtual environments and generated files out of commits.
