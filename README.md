# Aurora Sectorfile Link Installer (Windows)
This Windows app let's FIR and ATC Ops staff link a folder with a custom structure and link it to a Aurora installation. Thus, only editing on the git one and seeing the change right away on Aurora.

Small Windows tool to create link-based SectorFiles layout for Aurora during development.

Features
- Create directory junctions for Include\COnew and Include\COnew_2 pointing to your repo Include\COnew
- Link top-level .isc and .clr files into Aurora's SectorFiles folder (hardlink / symlink / mklink fallback)
- CLI and GUI front-end (Tkinter)
- Packable into a single .exe using PyInstaller

Quick start (local)
1. Clone repo or create folder and add files.
2. Create a virtualenv and install dependencies:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
3. Run GUI:
   python Development\gui.py
4. Or run CLI:
   python Development\cli.py --aurora "C:\Path\To\Aurora\SectorFiles" --repo "C:\Path\To\Repo\SectorFile-MAIN" --force

Build an exe (Windows)
1. Install PyInstaller:
   pip install pyinstaller
2. From repo root run:
   Development\build_exe.bat

See Development/build_exe.bat for exact pyinstaller invocation and notes.

License
- MIT