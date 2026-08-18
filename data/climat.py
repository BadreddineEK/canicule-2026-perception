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


def get_ete_villes() -> pd.DataFrame:
    return pd.read_csv(_ETE, encoding="utf-8")


def get_lyon_jour() -> pd.DataFrame:
    d = pd.read_csv(_LYON, encoding="utf-8", parse_dates=["time"])
    d["year"] = d["time"].dt.year
    d["month"] = d["time"].dt.month
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
        rows.append({
            "ville": ville,
            "anomalie_tmax": round(g.loc[ANNEE_COURANTE, "tmax_moy"] - normale(g["tmax_moy"]), 1),
            "nt_2026": int(g.loc[ANNEE_COURANTE, "nuits_trop"]),
            "nt_normale": round(normale(g["nuits_trop"]), 1),
            "tmax_rang": rang_annee(g["tmax_moy"]),
            "nt_rang": rang_annee(g["nuits_trop"]),
        })
    return pd.DataFrame(rows).sort_values("anomalie_tmax", ascending=False).reset_index(drop=True)
