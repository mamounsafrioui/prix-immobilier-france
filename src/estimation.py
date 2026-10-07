"""
Estimation du prix d'un appartement avec le modèle entraîné dans 02_modelisation.ipynb.
Utilisé par l'application Streamlit (app.py).
"""

from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "modele_prix.joblib"
GEOCODAGE_URL = "https://data.geopf.fr/geocodage/search/"
NOTRE_DAME = (48.8530, 2.3499)
DEPARTEMENTS = {"75", "92", "93", "94"}


def charger_modele(path: Path = MODEL_PATH) -> dict:
    return joblib.load(path)


def geocoder(adresse: str) -> dict | None:
    # API Adresse (Base Adresse Nationale), gratuite et sans clé
    r = requests.get(GEOCODAGE_URL, params={"q": adresse, "limit": 1}, timeout=10)
    r.raise_for_status()
    resultats = r.json().get("features", [])
    if not resultats:
        return None

    props = resultats[0]["properties"]
    lon, lat = resultats[0]["geometry"]["coordinates"]
    code_commune = props.get("citycode", "")
    # Paris peut revenir avec le code de la ville (75056) au lieu de celui de l'arrondissement
    if code_commune == "75056" and props.get("postcode", "").startswith("750"):
        code_commune = "751" + props["postcode"][-2:]

    return {"label": props.get("label", adresse), "latitude": lat, "longitude": lon,
            "code_commune": code_commune, "score": props.get("score", 0)}


def annees_depuis_2021(jour: date) -> float:
    return (jour - date(2021, 1, 1)).days / 365.25


def estimer(bundle: dict, surface: float, pieces: int, latitude: float, longitude: float,
            code_commune: str, jour: date | None = None) -> dict:
    jour = jour or date.today()
    dist = np.sqrt(((latitude - NOTRE_DAME[0]) * 111) ** 2 + ((longitude - NOTRE_DAME[1]) * 73) ** 2)

    X = pd.DataFrame({
        "surface": [surface],
        "pieces": [pieces],
        "latitude": [latitude],
        "longitude": [longitude],
        "dist_centre": [dist],
        "t": [annees_depuis_2021(jour)],
        "code_commune": pd.Categorical([code_commune]),
    })
    X["prix_quartier"] = bundle["knn_quartier"].predict(X[["latitude", "longitude"]])

    prix = float(np.exp(bundle["modele"].predict(X[bundle["features"]]))[0])
    return {
        "prix": prix,
        "prix_m2": prix / surface,
        "prix_m2_quartier": float(np.exp(X["prix_quartier"].iloc[0])),
    }
