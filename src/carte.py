"""
Cartes des prix au m² des appartements.

    python src/carte.py

Produit :
- reports/figures/carte_prix_m2.png  (carte fixe, affichée dans le README)
- reports/carte_prix_m2.html         (carte interactive Folium, à ouvrir dans un navigateur)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "dvf_clean.parquet"

# cases d'environ 400 m x 400 m
PAS_LAT = 0.0036
PAS_LON = 0.0055
MIN_VENTES = 10  # en dessous, la médiane d'une case n'est pas fiable


def grille(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(
        i=np.floor(df["latitude"] / PAS_LAT).astype(int),
        j=np.floor(df["longitude"] / PAS_LON).astype(int),
    )
    g = df.groupby(["i", "j"]).agg(prix_m2=("prix_m2", "median"), ventes=("prix_m2", "size")).reset_index()
    g = g[g["ventes"] >= MIN_VENTES]
    g["lat_min"] = g["i"] * PAS_LAT
    g["lon_min"] = g["j"] * PAS_LON
    return g


def carte_statique(g: pd.DataFrame, sortie: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 8.5))
    vmin, vmax = g["prix_m2"].quantile([0.02, 0.98])
    sc = ax.scatter(g["lon_min"] + PAS_LON / 2, g["lat_min"] + PAS_LAT / 2, c=g["prix_m2"],
                    cmap="RdYlBu_r", vmin=vmin, vmax=vmax, marker="s", s=22, linewidths=0)
    fig.colorbar(sc, ax=ax, shrink=0.7, label="Prix médian au m² (€)")

    reperes = {"Notre-Dame": (48.8530, 2.3499), "La Défense": (48.8918, 2.2362),
               "Saint-Denis": (48.9362, 2.3574), "Vincennes": (48.8474, 2.4392),
               "Boulogne": (48.8352, 2.2410), "Créteil": (48.7904, 2.4556)}
    for nom, (lat, lon) in reperes.items():
        ax.annotate(nom, (lon, lat), fontsize=9, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))

    ax.set_xlim(2.15, 2.62)
    ax.set_ylim(48.72, 48.96)
    ax.set_aspect(1 / np.cos(np.radians(48.86)))
    ax.set_axis_off()
    ax.set_title("Prix médian au m² des appartements (2021-2025), par carré de 400 m")
    fig.savefig(sortie, dpi=150, bbox_inches="tight")
    plt.close(fig)


def carte_interactive(g: pd.DataFrame, sortie: Path) -> None:
    import folium
    from branca.colormap import LinearColormap

    vmin, vmax = g["prix_m2"].quantile([0.02, 0.98])
    couleurs = LinearColormap(["#2c7bb6", "#ffffbf", "#d7191c"], vmin=vmin, vmax=vmax)
    couleurs.caption = "Prix médian au m² des appartements (€)"

    m = folium.Map(location=[48.86, 2.35], zoom_start=12, tiles="cartodbpositron")
    for c in g.itertuples():
        folium.Rectangle(
            bounds=[[c.lat_min, c.lon_min], [c.lat_min + PAS_LAT, c.lon_min + PAS_LON]],
            stroke=False,
            fill=True,
            fill_color=couleurs(min(max(c.prix_m2, vmin), vmax)),
            fill_opacity=0.65,
            tooltip=f"{c.prix_m2:,.0f} €/m² ({c.ventes} ventes)".replace(",", " "),
        ).add_to(m)
    couleurs.add_to(m)
    m.save(str(sortie))


if __name__ == "__main__":
    df = pd.read_parquet(DATA)
    g = grille(df[df["type_local"] == "Appartement"])
    print(len(g), "cases")

    carte_statique(g, ROOT / "reports" / "figures" / "carte_prix_m2.png")
    carte_interactive(g, ROOT / "reports" / "carte_prix_m2.html")
    print("cartes enregistrées dans reports/")
