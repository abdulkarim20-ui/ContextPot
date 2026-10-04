"""
Automated Build and Packaging Script for ContextPot.
Compiles standalone Portable and Installed executables using PyInstaller and Inno Setup,
organizes them into Portable/ and Installed/ directories, and cleans up build artifacts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
SETUP_ROOT = Path("X:/Playground/setup") if Path("X:/Playground/setup").is_dir() else ROOT_DIR.parent / "setup"
PORTABLE_DIR = SETUP_ROOT / "Portable"
INSTALLED_DIR = SETUP_ROOT / "Installed"
ASSETS_DIR = ROOT_DIR / "assets"
ICON_PATH = ASSETS_DIR / "app_logo.ico"


def find_iscc() -> Path | None:
    """Find Inno Setup Compiler (ISCC.exe) if installed."""
    # Check PATH
    iscc_path = shutil.which("iscc")
    if iscc_path:
        return Path(iscc_path)

    # Standard Windows install locations
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 7/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 7/ISCC.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def run_pyinstaller() -> Path:
    """Compile the single standalone executable with PyInstaller."""
    print("=" * 60)
    print("STEP 1: Compiling ContextPot executable with PyInstaller...")
    print("=" * 60)

    hidden_imports = [
        "PySide6.QtSvg",
        "PySide6.QtXml",
        "PySide6.QtNetwork",
        "PySide6.QtPrintSupport",
        "ctypes",
        "ctypes.wintypes",
        "threading",
        "json",
        "re",
        "app",
        "app.config",
        "app.core",
        "app.views",
        "app.views.explorer",
        "app.views.settings",
        "app.widgets",
        "app.widgets.drop_zone",
        "app.widgets.export_bar",
    ]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconsole",
        "--onefile",
        "--name",
        "ContextPot",
        "--icon",
        str(ICON_PATH),
        "--add-data",
        f"{ASSETS_DIR};assets",
    ]

    for h in hidden_imports:
        cmd.extend(["--hidden-import", h])

    cmd.append(str(ROOT_DIR / "main.py"))

    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller failed with return code {res.returncode}")

    built_exe = DIST_DIR / "ContextPot.exe"
    if not built_exe.is_file():
        raise FileNotFoundError(f"Expected compiled binary not found at {built_exe}")

    print(f"Successfully compiled: {built_exe} ({built_exe.stat().st_size // (1024*1024)} MB)")
    return built_exe


def setup_portable_package(built_exe: Path) -> Path:
    """Package the Portable Edition."""
    print("\n" + "=" * 60)
    print("STEP 2: Organizing Portable Edition...")
    print("=" * 60)

    PORTABLE_DIR.mkdir(parents=True, exist_ok=True)
    portable_exe = PORTABLE_DIR / "ContextPot-Portable.exe"
    shutil.copy2(built_exe, portable_exe)

    # Create portable.flag
    (PORTABLE_DIR / "portable.flag").write_text(
        "# ContextPot Portable Mode Indicator\n"
        "# When this file is present, user data is saved inside the local User_Data/ directory.\n",
        encoding="utf-8",
    )

    # Create Portable README
    (PORTABLE_DIR / "README_ContextPot.txt").write_text(
        "ContextPot - Portable Edition\n"
        "===========================\n\n"
        "Features:\n"
        "- 100% Self-Contained: Zero installation or admin rights required.\n"
        "- Local Data Storage: All your scanned repositories, export formats, ignore patterns,\n"
        "  and tree preferences are stored inside the adjacent 'User_Data' folder.\n"
        "- USB / External Drive Ready: Carry your personal developer workspace anywhere.\n\n"
        "To Run:\n"
        "Double-click 'ContextPot-Portable.exe'.\n",
        encoding="utf-8",
    )

    print(f"Portable edition ready at: {PORTABLE_DIR}")
    return portable_exe


def setup_installed_package(built_exe: Path) -> Path:
    """Package the Installed Edition."""
    print("\n" + "=" * 60)
    print("STEP 3: Organizing Installed Edition...")
    print("=" * 60)

    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)
    installed_exe = INSTALLED_DIR / "ContextPot.exe"
    shutil.copy2(built_exe, installed_exe)

    # Create Installed README
    (INSTALLED_DIR / "README.txt").write_text(
        "ContextPot - Installed Edition\n"
        "============================\n\n"
        "Features:\n"
        "- Standard Windows Application: Stores durable user data inside\n"
        "  %APPDATA%\\ContextPot\\User_Data, keeping application files clean.\n"
        "- Windows Integration: Start Menu and Desktop shortcuts, native taskbar grouping,\n"
        "  and full uninstaller support.\n\n"
        "Files:\n"
        "- ContextPot-Setup.exe : Run this to install ContextPot with Desktop and Start Menu shortcuts.\n"
        "- ContextPot.exe       : Standalone installed executable (runs directly using %APPDATA%).\n",
        encoding="utf-8",
    )

    # Build Setup Installer using Inno Setup if available
    iscc = find_iscc()
    if iscc:
        print(f"Found Inno Setup Compiler at: {iscc}")
        iss_script = create_inno_script(built_exe)
        iss_path = ROOT_DIR / "setup_script.iss"
        iss_path.write_text(iss_script, encoding="utf-8")

        print("Compiling Windows Installer (ContextPot-Setup.exe)...")
        res = subprocess.run([str(iscc), str(iss_path)], cwd=str(ROOT_DIR))
        if iss_path.exists():
            iss_path.unlink()

        if res.returncode == 0:
            setup_exe = INSTALLED_DIR / "ContextPot-Setup.exe"
            if setup_exe.is_file():
                print(f"Windows Setup Installer ready at: {setup_exe}")
                # Keep only the installer in Installed/ folder
                if installed_exe.is_file():
                    installed_exe.unlink()
        else:
            print("Warning: Inno Setup compilation returned non-zero code.")
    else:
        print("Note: Inno Setup compiler not detected. Skipping ContextPot-Setup.exe compilation.")

    print(f"Installed edition ready at: {INSTALLED_DIR}")
    return INSTALLED_DIR / "ContextPot-Setup.exe" if (INSTALLED_DIR / "ContextPot-Setup.exe").is_file() else installed_exe


def create_inno_script(exe_path: Path) -> str:
    """Generate Inno Setup script content."""
    license_file = ROOT_DIR / "LICENSE"
    license_line = f'LicenseFile={str(license_file).replace(os.sep, "/")}' if license_file.is_file() else ""

    return f"""
#define MyAppName "ContextPot"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "AbdulKarim"
#define MyAppURL "https://github.com/abdulkarim20-ui"
#define MyAppExeName "ContextPot.exe"
#define MyAppId "AbdulKarim.ContextPot.1.0"

[Setup]
AppId={{{{C8A415EE-CTXT-POT1-2026-ABK9942}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppVerName={{#MyAppName}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
{license_line}
OutputDir={str(INSTALLED_DIR).replace(os.sep, "/")}
OutputBaseFilename=ContextPot-Setup
SetupIconFile={str(ICON_PATH).replace(os.sep, "/")}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
SetupAppTitle=ContextPot Setup
SetupWindowTitle=ContextPot Setup

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "{str(exe_path).replace(os.sep, "/")}"; DestDir: "{{app}}"; DestName: "{{#MyAppExeName}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; AppUserModelID: "{{#MyAppId}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon; AppUserModelID: "{{#MyAppId}}"

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
"""


def cleanup_build_artifacts():
    """Remove intermediate build artifacts."""
    print("\n" + "=" * 60)
    print("STEP 4: Cleaning up temporary build directories...")
    print("=" * 60)

    # 1. Remove build directory
    if BUILD_DIR.is_dir():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        print(f"Removed temporary directory: {BUILD_DIR}")

    # 2. Remove spec file in root
    spec_file = ROOT_DIR / "ContextPot.spec"
    if spec_file.is_file():
        spec_file.unlink()
        print(f"Removed temporary spec file: {spec_file}")

    # 3. Clean up PyInstaller dist directory
    if DIST_DIR.is_dir():
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        print(f"Removed temporary directory: {DIST_DIR}")

    print("Build cleanup completed successfully!")


def main():
    try:
        portable_only = "--portable-only" in sys.argv or "-p" in sys.argv

        built_exe = run_pyinstaller()
        setup_portable_package(built_exe)
        if not portable_only:
            setup_installed_package(built_exe)
        cleanup_build_artifacts()

        print("\n" + "*" * 60)
        print("BUILD SUCCESSFUL!")
        print(f"1. Portable Version:  {PORTABLE_DIR / 'ContextPot-Portable.exe'}")
        if not portable_only:
            if (INSTALLED_DIR / "ContextPot-Setup.exe").is_file():
                print(f"2. Windows Installer: {INSTALLED_DIR / 'ContextPot-Setup.exe'}")
            elif (INSTALLED_DIR / "ContextPot.exe").is_file():
                print(f"2. Installed Version: {INSTALLED_DIR / 'ContextPot.exe'}")
        print("*" * 60)
    except Exception as exc:
        print(f"Build failed with error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
