"""Download Misaki Gothic BDF font for Japanese text rendering in Pyxel."""

import os
import io
import zipfile
import urllib.request

FONT_URL = "https://littlelimit.net/arc/misaki/misaki_bdf_2021-05-05.zip"
FONT_FILENAME = "misaki_gothic.bdf"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
FONT_PATH = os.path.join(ASSETS_DIR, FONT_FILENAME)


def download_font():
    """Download and extract misaki_gothic.bdf into assets/ folder."""
    if os.path.exists(FONT_PATH):
        print(f"[OK] Font already exists: {FONT_PATH}")
        return FONT_PATH

    os.makedirs(ASSETS_DIR, exist_ok=True)
    print(f"Downloading Misaki Gothic font from {FONT_URL} ...")

    try:
        req = urllib.request.Request(FONT_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        print("Please manually download from: https://littlelimit.net/misaki.htm")
        return None

    print("Extracting BDF font ...")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # BDFファイルを探す
            bdf_files = [n for n in zf.namelist() if n.endswith(".bdf")]
            # misaki_gothic を優先
            target = None
            for name in bdf_files:
                if "gothic" in name.lower():
                    target = name
                    break
            if target is None and bdf_files:
                target = bdf_files[0]

            if target is None:
                print("[ERROR] No BDF file found in the archive.")
                return None

            # 抽出
            with zf.open(target) as src, open(FONT_PATH, "wb") as dst:
                dst.write(src.read())

            print(f"[OK] Font saved to: {FONT_PATH}")
            return FONT_PATH

    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return None


if __name__ == "__main__":
    result = download_font()
    if result:
        print(f"\nReady! Font path: {result}")
    else:
        print("\nFont download failed. See errors above.")
