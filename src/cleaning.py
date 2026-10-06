"""
Chargement et nettoyage des données DVF.

Attention : une vente peut apparaître sur plusieurs lignes (appart + cave + parking...)
et chaque ligne contient le prix total. On ne garde donc que les ventes d'un seul logement.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

COLUMNS = [
    "id_mutation", "date_mutation", "nature_mutation", "valeur_fonciere",
    "code_postal", "code_commune", "nom_commune", "code_departement",
    "type_local", "surface_reelle_bati", "nombre_pieces_principales",
    "surface_terrain", "longitude", "latitude",
]

LOGEMENTS = ["Appartement", "Maison"]


def load_raw(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    files = sorted(raw_dir.glob("dvf_*.csv.gz"))
    if not files:
        raise FileNotFoundError(f"pas de fichiers dans {raw_dir}, lancer src/download_data.py")

    dfs = [
        pd.read_csv(f, usecols=COLUMNS, dtype={"code_postal": str, "code_commune": str,
                                                "code_departement": str}, low_memory=False)
        for f in files
    ]
    return pd.concat(dfs, ignore_index=True)


def keep_single_dwelling_sales(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["nature_mutation"] == "Vente"]

    logements = df[df["type_local"].isin(LOGEMENTS)]
    nb_logements = logements.groupby("id_mutation").size()
    ventes_simples = nb_logements[nb_logements == 1].index

    # on enlève aussi les ventes avec un local commercial
    autres_locaux = df.loc[df["type_local"] == "Local industriel. commercial ou assimilé", "id_mutation"]

    mask = logements["id_mutation"].isin(ventes_simples) & ~logements["id_mutation"].isin(autres_locaux)
    return logements[mask].copy()


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df["date_mutation"] = pd.to_datetime(df["date_mutation"])
    df["annee"] = df["date_mutation"].dt.year
    df["mois"] = df["date_mutation"].dt.month
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]
    return df


def remove_outliers(df: pd.DataFrame,
                    surface_min: float = 9, surface_max: float = 500,
                    q_low: float = 0.01, q_high: float = 0.99) -> pd.DataFrame:
    # surface entre 9 m2 (minimum légal) et 500 m2
    # prix au m2 entre les percentiles 1 et 99, par département et type de bien
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "longitude", "latitude"])
    df = df[df["surface_reelle_bati"].between(surface_min, surface_max)]

    groups = df.groupby(["code_departement", "type_local"])["prix_m2"]
    low = groups.transform(lambda s: s.quantile(q_low))
    high = groups.transform(lambda s: s.quantile(q_high))
    return df[df["prix_m2"].between(low, high)]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = keep_single_dwelling_sales(df)
    df = add_features(df)
    df = remove_outliers(df)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    raw = load_raw()
    print("lignes brutes :", len(raw))
    cleaned = clean(raw)
    print("après nettoyage :", len(cleaned))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "dvf_clean.parquet"
    cleaned.to_parquet(out, index=False)
    print("sauvegardé dans", out)
