import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_GDL_DIR = Path(r"C:\Programs\gallery-dl-v1.26.8")
DEFAULT_EXE_FILE = DEFAULT_GDL_DIR / "gallery-dl.exe"
DEFAULT_COOKIES_FILE = DEFAULT_GDL_DIR / "www.instagram.com_cookies.txt"
DEFAULT_CONFIG_FILE = DEFAULT_GDL_DIR / "gallery-dl.conf"
DEFAULT_DOWNLOAD_DIR = DEFAULT_GDL_DIR / "gallery-dl" / "instagram_stories"
DEFAULT_USER_AGENT = "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"


def build_command(
    url,
    gdl_dir=DEFAULT_GDL_DIR,
    exe_file=DEFAULT_EXE_FILE,
    cookies_file=DEFAULT_COOKIES_FILE,
    config_file=DEFAULT_CONFIG_FILE,
    download_dir=DEFAULT_DOWNLOAD_DIR,
    user_agent=DEFAULT_USER_AGENT,
):
    return [
        str(exe_file),
        "-c", str(config_file),
        "-o", "ciphers=chrome",
        "--user-agent", user_agent,
        "--cookies", str(cookies_file),
        "--write-metadata",
        "-d", str(download_dir),
        url,
    ]


def main():
    parser = argparse.ArgumentParser(description="Download a single Instagram story URL.")
    parser.add_argument("url", help="Instagram URL to download")
    parser.add_argument("--gdl-dir", type=Path, default=DEFAULT_GDL_DIR)
    parser.add_argument("--exe-file", type=Path, default=DEFAULT_EXE_FILE)
    parser.add_argument("--cookies-file", type=Path, default=DEFAULT_COOKIES_FILE)
    parser.add_argument("--config-file", type=Path, default=DEFAULT_CONFIG_FILE)
    parser.add_argument("--download-dir", type=Path, default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    exe_file = args.exe_file if args.exe_file.is_absolute() else (args.gdl_dir / args.exe_file)
    cookies_file = args.cookies_file if args.cookies_file.is_absolute() else (args.gdl_dir / args.cookies_file)
    config_file = args.config_file if args.config_file.is_absolute() else (args.gdl_dir / args.config_file)
    download_dir = args.download_dir if args.download_dir.is_absolute() else (args.gdl_dir / args.download_dir)

    if not exe_file.exists():
        print(f"gallery-dl executable not found: {exe_file}", file=sys.stderr)
        return 1

    download_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_command(
        url=args.url,
        exe_file=exe_file,
        cookies_file=cookies_file,
        config_file=config_file,
        download_dir=download_dir,
        user_agent=args.user_agent,
    )

    if args.dry_run:
        print(" ".join(cmd))
        return 0

    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
