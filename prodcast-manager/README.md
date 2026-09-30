# ProdCast Manager 0.5

Windows application for installing and updating ProdCast through SSH.

This directory contains the exact contents of `source.zip` shipped with `ProdCast-Manager-0.5.zip`, with this README added for repository navigation.

Source archive SHA-256: `366ef5bdbcb03ddfb0797b0403677f2686a7202196ced3af7e50ccbcd7fbfbb7`.

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

The build script runs tests, builds GUI and CLI executables, and checks packaged resources and GUI initialization. Output is written to `dist/`.

To run from source:

```powershell
.\.venv\Scripts\python.exe manager.py
```

Local profiles, credentials, caches and logs are not part of this source snapshot. Keep virtual environments and generated files out of commits.
