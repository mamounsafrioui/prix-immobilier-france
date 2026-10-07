"""
Application d'estimation du prix d'un appartement à Paris et en petite couronne.

    streamlit run app.py
"""

import pandas as pd
import streamlit as st

from src.estimation import DEPARTEMENTS, charger_modele, estimer, geocoder

st.set_page_config(page_title="Estimation appartement IDF")


@st.cache_resource
def modele():
    return charger_modele()


def euros(x: float) -> str:
    return f"{x:,.0f} €".replace(",", " ")


st.title("Combien vaut cet appartement ?")
st.write(
    "Estimation à partir des ventes réelles enregistrées entre 2021 et 2025 (données DVF), "
    "pour Paris, les Hauts-de-Seine, la Seine-Saint-Denis et le Val-de-Marne."
)

with st.form("estimation"):
    adresse = st.text_input("Adresse", placeholder="ex : 12 rue de la Roquette, Paris")
    col1, col2 = st.columns(2)
    surface = col1.number_input("Surface (m²)", min_value=9, max_value=500, value=45)
    pieces = col2.number_input("Nombre de pièces", min_value=1, max_value=10, value=2)
    valider = st.form_submit_button("Estimer")

if valider:
    if not adresse.strip():
        st.warning("Indique une adresse.")
        st.stop()

    try:
        lieu = geocoder(adresse)
    except Exception:
        st.error("Le service de géolocalisation ne répond pas, réessaie dans un instant.")
        st.stop()

    if lieu is None:
        st.error("Adresse introuvable.")
        st.stop()
    if lieu["code_commune"][:2] not in DEPARTEMENTS:
        st.error(f"« {lieu['label']} » est en dehors de la zone couverte (75, 92, 93, 94).")
        st.stop()

    res = estimer(modele(), surface, pieces, lieu["latitude"], lieu["longitude"], lieu["code_commune"])

    st.caption(f"Adresse retenue : {lieu['label']}")
    st.metric("Prix estimé", euros(res["prix"]))

    c1, c2 = st.columns(2)
    c1.metric("Soit au m²", euros(res["prix_m2"]))
    c2.metric("Prix moyen au m² du quartier", euros(res["prix_m2_quartier"]))

    st.write(
        f"Fourchette indicative : **{euros(res['prix'] * 0.88)} – {euros(res['prix'] * 1.12)}**. "
        "Sur les ventes de test, la moitié des appartements sont estimés à moins de 12 % près."
    )
    st.map(pd.DataFrame({"lat": [lieu["latitude"]], "lon": [lieu["longitude"]]}), zoom=14)

st.divider()
st.caption(
    "Le modèle ne connaît ni l'étage, ni l'état du bien, ni les équipements (balcon, ascenseur...). "
    "C'est une estimation statistique, pas une expertise. "
    "Code source : github.com/mamounsafrioui/prix-immobilier-france"
)
