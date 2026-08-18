"""
Construit un jeu de données climatique à partir de l'API archive Open-Meteo
(réanalyse ERA5, journalier depuis 1940, gratuite et sans clé).

Deux sorties :
  - data/ete_villes.csv : agrégats d'été par ville et par année (11 grandes villes)
  - data/lyon_jour.csv  : températures journalières de Lyon depuis 1950 (grain fin)

Comparaison honnête : tous les indicateurs d'été sont calculés sur la MÊME fenêtre
calendaire (1er juin → 17 août), pour que 2026 (arrêté au 17 août) soit comparable
aux étés complets des années précédentes.

Dépendance dev uniquement : requests.
"""

import time
from pathlib import Path
import requests
import pandas as pd

URL = "https://archive-api.open-meteo.com/v1/archive"
START = "1950-01-01"
END = "2026-08-17"
CACHE = Path("data/_cache")

# Ville de référence en tête, puis un panorama national.
VILLES = {
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


def fetch_ville(ville, lat, lon):
    """Récupère le journalier d'une ville, avec cache local et backoff sur 429."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"{ville}.csv"
    if cache.exists():
        d = pd.read_csv(cache, parse_dates=["time"])
        print("  (cache)")
        return d

    params = {
        "latitude": lat, "longitude": lon,
        "start_date": START, "end_date": END,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Europe/Paris",
    }
    for attempt in range(6):
        r = requests.get(URL, params=params, timeout=180)
        if r.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"  429, pause {wait}s...")
            time.sleep(wait)
            continue
        r.raise_for_status()
        d = pd.DataFrame(r.json()["daily"])
        d["time"] = pd.to_datetime(d["time"])
        d = d.rename(columns={"temperature_2m_max": "tmax", "temperature_2m_min": "tmin"})
        d.to_csv(cache, index=False)
        return d
    raise RuntimeError(f"Rate limit persistant pour {ville}")


def fenetre_ete(d):
    """Garde le 1er juin → 17 août (fenêtre comparable à 2026)."""
    m, j = d["time"].dt.month, d["time"].dt.day
    return d[(m.isin([6, 7])) | ((m == 8) & (j <= 17))].copy()


def agrege(d, ville):
    e = fenetre_ete(d)
    e["year"] = e["time"].dt.year
    g = e.groupby("year").agg(
        tmax_moy=("tmax", "mean"),
        tmin_moy=("tmin", "mean"),
        nuits_trop=("tmin", lambda s: int((s >= 20).sum())),
        jours_35=("tmax", lambda s: int((s >= 35).sum())),
        tx_abs=("tmax", "max"),
        tn_max=("tmin", "max"),
    ).reset_index()
    g.insert(0, "ville", ville)
    for c in ["tmax_moy", "tmin_moy", "tx_abs", "tn_max"]:
        g[c] = g[c].round(2)
    return g


def build():
    all_agg = []
    lyon_daily = None
    for ville, (lat, lon) in VILLES.items():
        print("→", ville)
        d = fetch_ville(ville, lat, lon)
        all_agg.append(agrege(d, ville))
        if ville == "Lyon":
            lyon_daily = d[["time", "tmax", "tmin"]].copy()
        time.sleep(8.0)  # rester poli avec l'API (limite de débit)

    ete = pd.concat(all_agg, ignore_index=True).sort_values(["ville", "year"])
    ete.to_csv("data/ete_villes.csv", index=False, encoding="utf-8")
    print("ete_villes.csv :", len(ete), "lignes,", ete["ville"].nunique(), "villes")

    lyon_daily["tmax"] = lyon_daily["tmax"].round(1)
    lyon_daily["tmin"] = lyon_daily["tmin"].round(1)
    lyon_daily.to_csv("data/lyon_jour.csv", index=False, encoding="utf-8")
    print("lyon_jour.csv :", len(lyon_daily), "lignes")


if __name__ == "__main__":
    build()
