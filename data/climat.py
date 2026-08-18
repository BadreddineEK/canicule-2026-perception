"""
Chargement et calculs sur les données climatiques (Open-Meteo / ERA5).

Deux jeux :
  - ete_villes.csv : agrégats d'été (1er juin → 17 août) par ville et par année
  - lyon_jour.csv  : températures journalières de Lyon depuis 1950

Référence « normale » : moyenne 1991-2020 (standard Météo-France).
"""

from pathlib import Path
import numpy as np
import pandas as pd

_ETE = Path(__file__).with_name("ete_villes.csv")
_LYON = Path(__file__).with_name("lyon_jour.csv")

VILLE_REF = "Lyon"
ANNEE_COURANTE = 2026
NORM_DEBUT, NORM_FIN = 1991, 2020

# Coordonnées des villes (pour la carte de France)
VILLES_COORDS = {
    "Lyon": (45.75, 4.85),
    "Paris": (48.8566, 2.3522),
    "Marseille": (43.2965, 5.3698),
    "Toulouse": (43.6045, 1.4440),
    "Bordeaux": (44.8378, -0.5792),
    "Nice": (43.7102, 7.2620),
    "Nantes": (47.2184, -1.5536),
    "Strasbourg": (48.5734, 7.7521),
    "Lille": (50.6292, 3.0573),
    "Montpellier": (43.6108, 3.8767),
    "Rennes": (48.1173, -1.6778),
}


def get_ete_villes() -> pd.DataFrame:
    return pd.read_csv(_ETE, encoding="utf-8")


def get_lyon_jour() -> pd.DataFrame:
    d = pd.read_csv(_LYON, encoding="utf-8", parse_dates=["time"])
    d["year"] = d["time"].dt.year
    d["month"] = d["time"].dt.month
    d["day"] = d["time"].dt.day
    return d


def normale(serie_par_annee: pd.Series) -> float:
    """Moyenne 1991-2020 d'une série indexée par année."""
    return float(serie_par_annee.loc[NORM_DEBUT:NORM_FIN].mean())


def tendance_par_decennie(years, values) -> float:
    """Pente linéaire (°C ou nuits) par décennie, robuste et lisible."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    if len(years) < 2:
        return 0.0
    a, _ = np.polyfit(years, values, 1)
    return float(a * 10)


def tendance_ic(years, values) -> dict:
    """Pente linéaire par décennie AVEC intervalle de confiance à 95 %.

    On mesure la pente d'une régression OLS et l'incertitude sur cette pente
    (erreur-type analytique). Sert à dire honnêtement si la tendance est
    statistiquement distinguable de zéro, pas seulement « visuellement montante ».
    """
    x = np.asarray(years, dtype=float)
    y = np.asarray(values, dtype=float)
    n = len(x)
    if n < 3:
        return {"pente_dec": 0.0, "lo": 0.0, "hi": 0.0, "significatif": False, "n": int(n)}
    a, b = np.polyfit(x, y, 1)
    resid = y - (a * x + b)
    sse = float(np.sum(resid ** 2))
    sxx = float(np.sum((x - x.mean()) ** 2))
    # erreur-type de la pente ; t*≈1.98 pour ~75 degrés de liberté (95 %)
    se = np.sqrt((sse / (n - 2)) / sxx) if sxx > 0 else 0.0
    t = 1.98
    lo, hi = (a - t * se) * 10, (a + t * se) * 10
    return {
        "pente_dec": a * 10,
        "lo": lo,
        "hi": hi,
        "significatif": bool(lo > 0 or hi < 0),
        "n": int(n),
    }


def anomalie_multi_ref(serie_par_annee: pd.Series, annee: int = ANNEE_COURANTE) -> pd.DataFrame:
    """Écart de l'année courante à la « normale », selon 3 périodes de référence.

    Test de robustesse : la conclusion (« bien au-dessus de la normale ») ne doit
    pas dépendre du choix arbitraire de la fenêtre de référence.
    """
    v = float(serie_par_annee.loc[annee])
    fenetres = {"1961-1990": (1961, 1990), "1981-2010": (1981, 2010), "1991-2020": (1991, 2020)}
    rows = []
    for label, (a, b) in fenetres.items():
        base = float(serie_par_annee.loc[a:b].mean())
        rows.append({"reference": label, "normale": round(base, 1), "anomalie": round(v - base, 1)})
    return pd.DataFrame(rows)


def nuits_seuils_lyon(lyon_jour: pd.DataFrame, seuils=(18, 20, 22), ville_annee: int = ANNEE_COURANTE) -> pd.DataFrame:
    """Recalcule les nuits chaudes de Lyon pour plusieurs seuils de Tmin.

    Test de robustesse : le rang record de 2026 tient-il si on change la
    définition (18, 20 ou 22 °C) ? Calcul direct sur les Tmin journalières,
    sur la même fenêtre comparable (1er juin → 17 août).
    """
    d = lyon_jour.copy()
    # On dérive year/month/day depuis `time` pour ne dépendre d'aucune colonne
    # pré-calculée (robuste à un cache Streamlit obsolète).
    t = pd.to_datetime(d["time"])
    d["year"], d["month"], d["day"] = t.dt.year, t.dt.month, t.dt.day
    d = d[(d["month"].isin([6, 7])) | ((d["month"] == 8) & (d["day"] <= 17))]
    rows = []
    for s in seuils:
        cnt = d.assign(nt=(d["tmin"] >= s)).groupby("year")["nt"].sum()
        val = int(cnt.loc[ville_annee])
        rows.append({
            "seuil": f"≥ {s} °C",
            "nt_2026": val,
            "normale": round(float(cnt.loc[NORM_DEBUT:NORM_FIN].mean()), 1),
            "rang": int((cnt > val).sum()) + 1,
            "n_annees": int(cnt.index.nunique()),
        })
    return pd.DataFrame(rows)


def rang_annee(serie_par_annee: pd.Series, annee: int = ANNEE_COURANTE) -> int:
    """Rang de l'année (1 = valeur la plus élevée)."""
    v = serie_par_annee.loc[annee]
    return int((serie_par_annee > v).sum()) + 1


def resume_ville(ete: pd.DataFrame, ville: str) -> dict:
    """Chiffres clés d'une ville pour l'année courante vs la normale."""
    g = ete[ete["ville"] == ville].set_index("year")
    return {
        "nt_2026": int(g.loc[ANNEE_COURANTE, "nuits_trop"]),
        "nt_normale": round(normale(g["nuits_trop"]), 1),
        "nt_rang": rang_annee(g["nuits_trop"]),
        "tmax_2026": float(g.loc[ANNEE_COURANTE, "tmax_moy"]),
        "tmax_normale": round(normale(g["tmax_moy"]), 1),
        "tmax_anomalie": round(g.loc[ANNEE_COURANTE, "tmax_moy"] - normale(g["tmax_moy"]), 1),
        "tmax_rang": rang_annee(g["tmax_moy"]),
        "jours35_2026": int(g.loc[ANNEE_COURANTE, "jours_35"]),
        "jours35_normale": round(normale(g["jours_35"]), 1),
        "n_annees": int(g.index.nunique()),
    }


def panorama_villes(ete: pd.DataFrame) -> pd.DataFrame:
    """Anomalie de Tmax et record de nuits tropicales par ville pour 2026."""
    rows = []
    for ville, g in ete.groupby("ville"):
        g = g.set_index("year")
        lat, lon = VILLES_COORDS.get(ville, (None, None))
        rows.append({
            "ville": ville,
            "lat": lat,
            "lon": lon,
            "anomalie_tmax": round(g.loc[ANNEE_COURANTE, "tmax_moy"] - normale(g["tmax_moy"]), 1),
            "nt_2026": int(g.loc[ANNEE_COURANTE, "nuits_trop"]),
            "nt_normale": round(normale(g["nuits_trop"]), 1),
            "tmax_rang": rang_annee(g["tmax_moy"]),
            "nt_rang": rang_annee(g["nuits_trop"]),
        })
    return pd.DataFrame(rows).sort_values("anomalie_tmax", ascending=False).reset_index(drop=True)


def france_par_annee(ete: pd.DataFrame) -> pd.DataFrame:
    """Moyenne nationale (des villes suivies) par année : la vue France entière."""
    f = ete.groupby("year").agg(
        nuits_trop=("nuits_trop", "mean"),
        tmax_moy=("tmax_moy", "mean"),
    ).reset_index()
    f["nuits_trop"] = f["nuits_trop"].round(1)
    f["tmax_moy"] = f["tmax_moy"].round(2)
    f["ville"] = "France (11 villes)"
    return f
