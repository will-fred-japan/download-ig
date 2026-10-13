# single_story.py
# -*- coding: utf-8 -*-

import sys
import subprocess
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: single_story.py <instagram_url>")
    sys.exit(1)

url = sys.argv[1]

# Base directory for config/cookies and exe
GDL_DIR = Path(r"C:\Programs\gallery-dl-v1.26.8")

EXE_FILE     = GDL_DIR / "gallery-dl.exe"
COOKIES_FILE = GDL_DIR / "www.instagram.com_cookies.txt"
CONFIG_FILE  = GDL_DIR / "gallery-dl.conf"
DOWNLOAD_DIR = Path(r"C:\Programs\gallery-dl-v1.26.8\gallery-dl\instagram_stories")

cmd = [
    str(EXE_FILE),             # absolute path to exe
    # "-v",
    "-c", str(CONFIG_FILE),
    "-o", "ciphers=chrome",
    "--user-agent", "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "--cookies", str(COOKIES_FILE),
    "--write-metadata",
    "-d", str(DOWNLOAD_DIR),
    url,
]

subprocess.run(cmd, check=False)
