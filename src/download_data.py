"""
Télécharge les fichiers DVF géolocalisés (data.gouv.fr) par année et par département.

    python src/download_data.py
    python src/download_data.py --deps 75 92 --years 2023 2024
"""

import argparse
from pathlib import Path

import requests
from tqdm import tqdm

BASE_URL = "https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/{dep}.csv.gz"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

DEFAULT_DEPS = ["75", "92", "93", "94"]
DEFAULT_YEARS = [2021, 2022, 2023, 2024, 2025]


def download_file(url: str, dest: Path) -> bool:
    # renvoie False si le fichier n'existe pas (année pas encore publiée par exemple)
    response = requests.get(url, stream=True, timeout=60)
    if response.status_code == 404:
        return False
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            f.write(chunk)
            bar.update(len(chunk))
    return True


def main(deps: list[str], years: list[int]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for year in years:
        for dep in deps:
            dest = RAW_DIR / f"dvf_{year}_{dep}.csv.gz"
            if dest.exists():
                print(f"{dest.name} déjà présent")
                continue

            url = BASE_URL.format(year=year, dep=dep)
            if download_file(url, dest):
                print(f"{dest.name} ok")
            else:
                print(f"{year} / {dep} : pas disponible")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deps", nargs="+", default=DEFAULT_DEPS)
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    args = parser.parse_args()
    main(args.deps, args.years)
