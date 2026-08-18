# 🌡️ Canicule 2026 : vraie ou impression ?

> *« On a tous eu la sensation d'un été 2026 étouffant, surtout la nuit. Alors j'ai arrêté de deviner et je suis allé voir la donnée, depuis 1950. »*

Un dashboard Streamlit qui tranche une question que tout le monde s'est posée cet été : **a-t-il vraiment fait exceptionnellement chaud, ou est-ce une impression ?** Réponse par la donnée ouverte, sans modèle, juste des faits mesurés — avec un focus sur la métrique la plus parlante : les **nuits tropicales**.

## 🎯 Ce que montre le dashboard

- **La réponse d'entrée** : à Lyon, l'été 2026 est le plus chaud depuis 1950, avec **47 nuits tropicales** (Tmin ≥ 20 °C) contre ~7 en temps normal.
- **Le graphique qui tranche** : nuits tropicales par année, interactif par ville.
- **Le panorama national** : 11 grandes villes, toutes à leur record de chaleur estivale en 2026 (+4 à +6 °C vs normale).
- **Accident ou tendance ?** : pente de fond (°C / décennie) et glissement de toute la distribution des températures.
- **Le pont** vers le chapitre 2 : l'îlot de chaleur urbain de Lyon, au grain de la rue.

## 📊 Données & méthode

- **Source** : API archive [Open-Meteo](https://open-meteo.com), réanalyse **ERA5** (ECMWF), journalier depuis 1950. Gratuite, reproductible, une seule source cohérente pour toutes les années.
- **Fenêtre comparable** : tous les indicateurs d'été sont calculés sur le **1er juin → 17 août**, pour comparer équitablement 2026 (tronqué) aux étés passés.
- **Normale** : moyenne **1991-2020** (référence Météo-France).
- **Pas de ML** : le sujet ne le demande pas. Que des statistiques honnêtes (écarts à la normale, tendances linéaires, distributions).

## 🛠️ Stack

Python 3.12 · Streamlit · Pandas · NumPy · Plotly

## 🚀 Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🔄 Reproduire les données

Les CSV sont versionnés (`data/ete_villes.csv`, `data/lyon_jour.csv`), l'app fonctionne sans rien télécharger. Pour les régénérer :

```bash
pip install requests
python data/build_climat.py
```

Le script interroge Open-Meteo pour 11 villes (1950-2026), avec cache local et backoff sur la limite de débit. `requests` n'est utilisé que par ce script.

## 📁 Structure

```
├── app.py                    # App Streamlit
├── data/
│   ├── ete_villes.csv        # Agrégats d'été par ville et année (11 villes) — versionné
│   ├── lyon_jour.csv         # Températures journalières de Lyon depuis 1950 — versionné
│   ├── climat.py             # Chargement + calculs (normale, tendance, panorama)
│   └── build_climat.py       # Génération depuis Open-Meteo (dev)
├── utils/
│   └── viz.py                # Graphiques Plotly
├── .streamlit/config.toml
├── .python-version
├── requirements.txt
└── README.md
```

---

*Badreddine EL KHAMLICHI · Ingénieur en mathématiques appliquées · Lyon · [badreddineek.com](https://badreddineek.com)*
