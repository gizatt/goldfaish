import requests
import tarfile
from pathlib import Path

FORGE_URL = "https://github.com/Card-Forge/forge/releases/download/forge-2.0.04/forge-installer-2.0.04.tar.bz2"
DEST_DIR = Path("sandbox/forge")
TAR_PATH = DEST_DIR / "forge-installer-2.0.04.tar.bz2"


def download_forge():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    if not TAR_PATH.exists():
        print(f"Downloading Forge from {FORGE_URL}...")
        with requests.get(FORGE_URL, stream=True) as r:
            r.raise_for_status()
            with open(TAR_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
    else:
        print("Forge archive already downloaded.")

    print("Extracting Forge...")
    with tarfile.open(TAR_PATH, "r:bz2") as tar:
        tar.extractall(path=DEST_DIR)
    print(f"Forge extracted to {DEST_DIR.resolve()}")

if __name__ == "__main__":
    download_forge()
