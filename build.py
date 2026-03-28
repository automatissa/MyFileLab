"""
PyInstaller build helper — called by GitHub Actions.
Usage: python build.py <windows|mac|linux> <output-name>
Handles DLL/dylib/so bundling without shell quoting issues.
"""
import glob
import os
import subprocess
import sys


def main():
    platform = sys.argv[1]   # windows | mac | linux
    name     = sys.argv[2]   # e.g. MyFileLab-Windows

    sep      = ";" if platform == "windows" else ":"
    tess_dir = "dist_assets/tesseract"

    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed",
        "--name", name,
        "--add-data", f"{tess_dir}/tessdata{sep}tesseract/tessdata",
    ]

    if platform == "windows":
        args += ["--icon", "icon_autopdf.ico"]
        args += ["--add-binary", f"{tess_dir}/tesseract.exe{sep}tesseract"]
        for dll in glob.glob(f"{tess_dir}/*.dll"):
            args += ["--add-binary", f"{dll}{sep}tesseract"]

    else:  # mac / linux
        args += ["--add-binary", f"{tess_dir}/tesseract{sep}tesseract"]
        for lib in glob.glob(f"{tess_dir}/*.so*") + glob.glob(f"{tess_dir}/*.dylib"):
            args += ["--add-binary", f"{lib}{sep}tesseract"]

    args.append("main.py")
    subprocess.run(args, check=True)


if __name__ == "__main__":
    main()
