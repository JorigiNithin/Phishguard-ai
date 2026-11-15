"""Download and prepare a URL phishing dataset.

Uses the well-known "phishing_site_urls.csv" dataset from Kaggle / academic sources.
The dataset contains URLs labelled as 'good' or 'bad'.

If the CSV is not found locally, this script generates a synthetic benchmark
dataset derived from common phishing URL patterns documented in the research
literature.  The synthetic data is ONLY used as a fallback – genuine datasets
are always preferred.

Source: "Phishing Site URLs" dataset (Kaggle)
  - ~550 000 labelled URLs
  - Labels: "good" (legitimate), "bad" (phishing)
  - Public domain / CC0

Place the CSV at: datasets/phishing_site_urls.csv
"""

from __future__ import annotations

import csv
import hashlib
import os
import random
import sys
from pathlib import Path

# Allow imports from the backend package
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

_PROJECT_ROOT = _BACKEND_DIR.parent
_DATASETS_DIR = _PROJECT_ROOT / "datasets"
_RAW_CSV = _DATASETS_DIR / "phishing_site_urls.csv"
_CLEAN_CSV = _DATASETS_DIR / "url_dataset_clean.csv"

# ---------------------------------------------------------------------------
# Synthetic fallback generator
# ---------------------------------------------------------------------------

_LEGIT_DOMAINS = [
    "google.com", "github.com", "stackoverflow.com", "wikipedia.org",
    "amazon.com", "microsoft.com", "apple.com", "linkedin.com",
    "youtube.com", "reddit.com", "twitter.com", "facebook.com",
    "netflix.com", "medium.com", "nytimes.com", "bbc.com",
    "cnn.com", "mozilla.org", "python.org", "npmjs.com",
    "docker.com", "ubuntu.com", "debian.org", "archlinux.org",
]

_LEGIT_PATHS = [
    "", "/", "/about", "/login", "/search?q=test", "/docs",
    "/help", "/contact", "/products", "/blog", "/news",
    "/en/docs/guide", "/user/settings", "/api/v1",
]

_PHISH_PATTERNS = [
    "http://{rand}.{tld}/login/verify?id={nonce}",
    "http://{ip}/secure/update-account/{nonce}",
    "https://{rand}-{brand}.{tld}/signin/confirm",
    "http://{brand}.{rand}.{tld}/password/reset?token={nonce}",
    "http://{brand}-verify.{tld}/account/suspended/{nonce}",
    "http://{rand}.{tld}/{brand}/credential/{nonce}",
    "http://{ip}/{brand}/login.php?session={nonce}",
    "https://{rand}.{tld}/webscr?cmd=login-submit&dispatch={nonce}",
    "http://{rand}.{tld}/banking-secure/confirm/{nonce}",
    "http://{brand}-authenticate.{tld}:8080/verify/{nonce}",
]

_BRANDS = ["paypal", "apple", "microsoft", "google", "amazon", "netflix", "chase", "wellsfargo"]
_RANDOM_TLDS = ["xyz", "tk", "ml", "ga", "cf", "top", "buzz", "info", "click", "link"]


def _rand_str(length: int = 8) -> str:
    return hashlib.md5(random.randbytes(8)).hexdigest()[:length]


def _rand_ip() -> str:
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def _generate_synthetic(n_legit: int = 5000, n_phish: int = 5000) -> list[tuple[str, str]]:
    """Generate synthetic labelled URLs for training."""
    rng = random.Random(42)
    rows: list[tuple[str, str]] = []

    # Legitimate URLs
    for _ in range(n_legit):
        domain = rng.choice(_LEGIT_DOMAINS)
        path = rng.choice(_LEGIT_PATHS)
        scheme = rng.choice(["https://", "https://", "https://", "http://"])
        sub = rng.choice(["", "www.", "app.", "docs.", "mail.", ""])
        url = f"{scheme}{sub}{domain}{path}"
        rows.append((url, "good"))

    # Phishing URLs
    for _ in range(n_phish):
        pattern = rng.choice(_PHISH_PATTERNS)
        url = pattern.format(
            rand=_rand_str(rng.randint(5, 12)),
            tld=rng.choice(_RANDOM_TLDS),
            ip=_rand_ip(),
            brand=rng.choice(_BRANDS),
            nonce=_rand_str(rng.randint(16, 32)),
        )
        rows.append((url, "bad"))

    rng.shuffle(rows)
    return rows


# ---------------------------------------------------------------------------
# Main preparation logic
# ---------------------------------------------------------------------------


def prepare_dataset() -> Path:
    """Load or generate the dataset, clean it, and write a clean CSV."""
    _DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, str]] = []

    if _RAW_CSV.exists():
        print(f"[dataset] Loading raw CSV from {_RAW_CSV}")
        with open(_RAW_CSV, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                raise ValueError("CSV is empty")
            # Detect columns
            header_lower = [h.strip().lower() for h in header]
            url_col = None
            label_col = None
            for i, h in enumerate(header_lower):
                if h in ("url", "urls", "uri"):
                    url_col = i
                elif h in ("label", "class", "type", "status", "result"):
                    label_col = i
            if url_col is None or label_col is None:
                # Fallback: assume first=URL, last=label
                url_col = 0
                label_col = len(header) - 1
            for row in reader:
                if len(row) <= max(url_col, label_col):
                    continue
                url = row[url_col].strip()
                label = row[label_col].strip().lower()
                if url and label in ("good", "bad", "legitimate", "phishing",
                                      "benign", "malicious", "0", "1"):
                    # Normalise label
                    if label in ("good", "legitimate", "benign", "0"):
                        label = "good"
                    else:
                        label = "bad"
                    rows.append((url, label))
        print(f"[dataset] Loaded {len(rows)} rows from CSV")
    else:
        print(f"[dataset] Raw CSV not found at {_RAW_CSV}")
        print("[dataset] Generating synthetic dataset (10 000 URLs)…")
        rows = _generate_synthetic(5000, 5000)
        print(f"[dataset] Generated {len(rows)} synthetic URLs")

    # --- Cleaning ---
    seen: set[str] = set()
    clean: list[tuple[str, str]] = []
    for url, label in rows:
        if not url or len(url) < 5:
            continue
        if url in seen:
            continue
        seen.add(url)
        clean.append((url, label))

    n_good = sum(1 for _, l in clean if l == "good")
    n_bad = sum(1 for _, l in clean if l == "bad")

    print(f"[dataset] After cleaning: {len(clean)} URLs (good={n_good}, bad={n_bad})")

    # Write clean CSV
    with open(_CLEAN_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        writer.writerows(clean)

    print(f"[dataset] Clean CSV written to {_CLEAN_CSV}")
    return _CLEAN_CSV


if __name__ == "__main__":
    prepare_dataset()

