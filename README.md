# Prix de l'immobilier en Île-de-France

Analyse des ventes immobilières à Paris et en petite couronne à partir des données DVF (Demandes de Valeurs Foncières), publiées par la DGFiP sur data.gouv.fr. L'objectif à terme est d'avoir un modèle capable d'estimer le prix d'un appartement à partir de sa surface, de son nombre de pièces et de sa localisation.

**Avancement :** l'analyse exploratoire est terminée. La partie modélisation est en cours.

## Données

J'utilise la version géolocalisée des DVF ([lien](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/)), qui recense toutes les ventes immobilières avec leurs coordonnées GPS.

- Départements : Paris (75), Hauts-de-Seine (92), Seine-Saint-Denis (93), Val-de-Marne (94)
- Période : 2021 à 2025
- Volume : 1,29 million de lignes brutes, 368 501 ventes gardées après nettoyage (321 366 appartements et 47 135 maisons)

Les fichiers sont trop lourds pour être mis sur GitHub, ils se téléchargent avec `src/download_data.py`.

## Le nettoyage

C'est la partie qui m'a pris le plus de temps à comprendre. Dans les DVF, une vente (une « mutation ») peut être répartie sur plusieurs lignes : l'appartement, la cave, la place de parking, parfois un deuxième lot. Le problème, c'est que chaque ligne reprend le **prix total** de la vente. Si on calcule un prix au m² ligne par ligne, on obtient des valeurs complètement fausses.

J'ai donc gardé uniquement :
- les ventes classiques (pas les échanges ni les adjudications) ;
- les ventes qui contiennent un seul logement, appartement ou maison ;
- les biens entre 9 et 500 m² ;
- les prix au m² compris entre le 1er et le 99e percentile, calculés par département et par type de bien.

Au final, moins d'un tiers des lignes de départ sont exploitables.

## Résultats

### Paris coûte 2,5 fois plus cher que la Seine-Saint-Denis

Prix médian au m² des appartements sur la période :

| Département | Prix médian au m² |
|---|---|
| Paris | 10 234 € |
| Hauts-de-Seine | 6 781 € |
| Val-de-Marne | 4 903 € |
| Seine-Saint-Denis | 4 000 € |

![Prix médian par département](reports/figures/prix_median_departement.png)

### Les prix baissent depuis 2022

| Département | Plus haut | 2024 | Variation | 2025 |
|---|---|---|---|---|
| Paris | 10 810 € (2021) | 9 533 € | −11,8 % | 9 667 € |
| Hauts-de-Seine | 7 121 € (2022) | 6 360 € | −10,7 % | 6 407 € |
| Val-de-Marne | 5 167 € (2022) | 4 651 € | −10,0 % | 4 734 € |
| Seine-Saint-Denis | 4 179 € (2022) | 3 856 € | −7,7 % | 3 974 € |

Ce sont les départements les plus chers qui ont le plus baissé. La chute correspond à la hausse des taux d'emprunt en 2022-2023. En 2025, les prix remontent un peu partout, mais il faut rester prudent : les données de l'année la plus récente ne sont pas toujours complètes.

![Évolution des prix](reports/figures/evolution_prix.png)

### Maisons et appartements : un piège dans la comparaison

Le prix médian au m² est de 5 110 € pour les maisons et de 7 647 € pour les appartements. On pourrait conclure que les maisons sont moins chères, mais c'est un effet de composition : les maisons se trouvent presque toutes en petite couronne, là où les prix sont plus bas, alors qu'à Paris on ne vend quasiment que des appartements. Pour comparer correctement, il faut raisonner à localisation égale, ce que fera le modèle.

![Prix par arrondissement](reports/figures/prix_arrondissements.png)

## Organisation du projet

```
prix-immobilier-france/
├── data/
│   ├── raw/              # fichiers DVF téléchargés (non versionnés)
│   └── processed/        # données nettoyées (non versionnées)
├── notebooks/
│   └── 01_exploration.ipynb
├── src/
│   ├── download_data.py
│   └── cleaning.py
├── reports/figures/
├── requirements.txt
└── README.md
```

## Lancer le projet

```bash
git clone https://github.com/<username>/prix-immobilier-france.git
cd prix-immobilier-france

conda create -n immo python=3.11 -y
conda activate immo
pip install -r requirements.txt

python src/download_data.py
```

Ensuite, ouvrir `notebooks/01_exploration.ipynb`.

## Suite du projet

- [ ] Modèle de prédiction : régression linéaire comme base, puis Random Forest et XGBoost
- [ ] Carte des prix au m² avec Folium
- [ ] Petite application Streamlit pour estimer un bien

## Outils

Python, Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, XGBoost, Folium, Streamlit

---

Mamoun Safrioui, étudiant ingénieur en data science à CY Tech
