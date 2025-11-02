import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INGESTED_DIR = DATA_DIR / "ingested"
METADATA_FILE = DATA_DIR / "metadata.json"


def load_sources():
    with open(DATA_DIR / "government-sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def download(name: str, url: str) -> Path:
    raw_path = RAW_DIR / f"{name}.txt"
    with urlopen(url) as resp:
        content = resp.read()
    raw_path.write_bytes(content)
    return raw_path


def normalize(raw_path: Path) -> Path:
    processed_path = PROCESSED_DIR / raw_path.name
    text = raw_path.read_text(errors="ignore")
    cleaned = " ".join(text.split())
    processed_path.write_text(cleaned)
    return processed_path


def compute_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_metadata() -> dict:
    if METADATA_FILE.exists():
        return json.loads(METADATA_FILE.read_text())
    return {}


def save_metadata(data: dict) -> None:
    METADATA_FILE.write_text(json.dumps(data, indent=2))


def already_ingested(name: str, digest: str, meta: dict) -> bool:
    entry = meta.get(name)
    return entry is not None and entry.get("hash") == digest


def ingest(processed_path: Path) -> None:
    for target in [INGESTED_DIR / "qdrant", INGESTED_DIR / "neo4j", INGESTED_DIR / "postgres"]:
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy(processed_path, target / processed_path.name)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    INGESTED_DIR.mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    metadata = load_metadata()

    for name, url in list(sources.items())[:3]:
        try:
            raw_path = download(name, url)
            digest = compute_hash(raw_path)
            if already_ingested(name, digest, metadata):
                print(f"Skipping {name}: no changes detected")
                continue
            processed_path = normalize(raw_path)
            ingest(processed_path)
            metadata[name] = {
                "hash": digest,
                "raw": str(raw_path),
                "processed": str(processed_path),
                "ingested_at": datetime.utcnow().isoformat(),
            }
            print(f"Processed {name}")
        except Exception as exc:
            print(f"Failed {name}: {exc}")

    save_metadata(metadata)


if __name__ == "__main__":
    main()
