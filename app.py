"""
App Streamlit — Canicule 2026 : vraie ou impression ?

On part d'une sensation (« il a fait anormalement chaud, surtout la nuit ») et on la
tranche avec la donnée : nuits tropicales, écart à la normale 1991-2020, tendance de
fond, à Lyon, dans ta ville et à l'échelle de la France. Données ouvertes Open-Meteo
(réanalyse ERA5), 1950 → 2026. Zéro modèle, que des faits mesurés.
"""

import streamlit as st

from data.climat import (
    get_ete_villes, get_lyon_jour, resume_ville, panorama_villes,
    france_par_annee, tendance_par_decennie, tendance_ic,
    anomalie_multi_ref, nuits_seuils_lyon, VILLE_REF,
)
from utils.viz import (
    plot_nuits_tropicales, plot_panorama, plot_distribution_decennies, plot_tendance,
    plot_carte_france, plot_france_trend,
)

ICU_URL = "https://canicule-lyon-model.streamlit.app/"

st.set_page_config(page_title="Canicule 2026 : vraie ou impression ?", page_icon="🌡️", layout="wide")

# Compteur remis à zéro à chaque rerun (le script se réexécute de haut en bas) :
# garantit une clé unique par graphique et évite StreamlitDuplicateElementId
# quand deux sections affichent un graphique identique (ex. la tendance de Lyon).
_PLOT_SEQ = {"n": 0}


def safe_plot(fig_func, *args, **kwargs):
    _PLOT_SEQ["n"] += 1
    try:
        st.plotly_chart(fig_func(*args, **kwargs), use_container_width=True,
                        key=f"chart_{_PLOT_SEQ['n']}")
    except Exception as e:
        st.warning("Ce graphique n'a pas pu être généré. Le reste de l'analyse reste disponible.")
        with st.expander("Détails techniques"):
            st.exception(e)


def get_active_theme() -> str:
    try:
        base = st.get_option("theme.base")
        if base in ("light", "dark"):
            return base
    except Exception:
        pass
    return "light"


@st.cache_data(show_spinner=False)
def load():
    ete = get_ete_villes()
    lyon = get_lyon_jour()
    pano = panorama_villes(ete)
    france = france_par_annee(ete)
    return ete, lyon, pano, france


try:
    ete, lyon, pano, france = load()
except Exception:
    st.error("Impossible de charger les données. Vérifiez `pip install -r requirements.txt`.")
    st.stop()

theme = get_active_theme()
villes = ete["ville"].unique().tolist()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.title("🌡️ Cet été, vraie canicule ou simple impression ?")
st.subheader(
    "On a tous eu la sensation d'un été 2026 étouffant, surtout la nuit. "
    "Alors j'ai arrêté de deviner et je suis allé voir la donnée, depuis 1950."
)
st.caption(
    "Par [Badreddine EL KHAMLICHI](https://badreddineek.com) · ingénieur en mathématiques appliquées, Lyon · "
    "[Portfolio](https://portfolio.badreddineek.com)"
)

st.caption(
    "🟢 **Lecture express (30 s)** : les titres, les chiffres et un graphique par section suffisent. "
    "🔬 **Envie de preuve ?** Dépliez les volets « Creuser » : robustesse statistique, sensibilité des "
    "seuils, et ce que la donnée permet — ou non — d'affirmer."
)

st.divider()

# ─────────────────────────────────────────
# SECTION 1 : LA RÉPONSE, TOUT DE SUITE (Lyon, héros)
# ─────────────────────────────────────────
r = resume_ville(ete, VILLE_REF)

st.markdown("## ✅ La réponse est nette : ce n'était pas dans ta tête")

st.markdown(
    f"À **Lyon**, l'été 2026 (au 17 août) est le **plus chaud depuis 1950**, et de loin. "
    "Le plus parlant, ce n'est pas le pic de l'après-midi : c'est que **la nuit ne refroidit plus**."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Nuits tropicales 2026", f"{r['nt_2026']}", f"normale : {r['nt_normale']:.0f}")
c2.metric("Chaleur max moyenne", f"{r['tmax_2026']:.1f} °C", f"+{r['tmax_anomalie']:.1f} °C vs normale")
c3.metric("Jours ≥ 35 °C", f"{r['jours35_2026']}", f"normale : {r['jours35_normale']:.0f}")
c4.metric("Classement de l'été", f"1er / {r['n_annees']}", "depuis 1950")

st.info(
    f"Une **nuit tropicale**, c'est une nuit où le thermomètre ne descend pas sous **20 °C**. "
    f"À Lyon, il y en a d'habitude {r['nt_normale']:.0f} par été. En 2026 : **{r['nt_2026']}**. "
    "C'est ça, la sensation de ne jamais récupérer.",
    icon="🌙",
)

st.divider()

# ─────────────────────────────────────────
# SECTION 2 : ET DANS TA VILLE ? (interactif)
# ─────────────────────────────────────────
st.markdown("## 🏙️ Et dans ta ville ?")
st.markdown("Choisis ta ville : les chiffres, le graphique et la tendance s'adaptent.")

ville = st.selectbox("Ta ville", villes, index=villes.index(VILLE_REF), label_visibility="collapsed")
rv = resume_ville(ete, ville)

v1, v2, v3, v4 = st.columns(4)
v1.metric("Nuits tropicales 2026", f"{rv['nt_2026']}", f"normale : {rv['nt_normale']:.0f}")
v2.metric("Chaleur max moyenne", f"{rv['tmax_2026']:.1f} °C", f"+{rv['tmax_anomalie']:.1f} °C")
v3.metric("Jours ≥ 35 °C", f"{rv['jours35_2026']}", f"normale : {rv['jours35_normale']:.0f}")
v4.metric("Rang nuits tropicales", f"{rv['nt_rang']}e / {rv['n_annees']}", "depuis 1950")

col_nt, col_tr = st.columns(2)
with col_nt:
    safe_plot(plot_nuits_tropicales, ete, ville, theme)
with col_tr:
    safe_plot(plot_tendance, ete, ville, "tmax_moy", f"Chaleur estivale à {ville} : la pente de fond", theme)

pente_nt = tendance_par_decennie(
    ete[ete["ville"] == ville]["year"], ete[ete["ville"] == ville]["nuits_trop"]
)
st.markdown(
    f"À **{ville}**, 2026 compte **{rv['nt_2026']} nuits tropicales** contre **{rv['nt_normale']:.0f}** "
    f"en temps normal (rang {rv['nt_rang']} sur {rv['n_annees']}). Ce n'est pas un pic isolé : "
    f"la tendance des nuits monte de **{pente_nt:+.1f} par décennie**."
)

st.divider()

# ─────────────────────────────────────────
# SECTION 3 : VUE NATIONALE — LA CARTE
# ─────────────────────────────────────────
st.markdown("## 🇫🇷 Un été record dans les grandes villes de France")

st.markdown(
    "Ce n'est pas qu'un ressenti lyonnais. Sur **11 grandes villes** (un échantillon, pas la France "
    "surfacique), l'été 2026 est **l'été le plus chaud jamais mesuré**, partout, depuis 1950. La "
    "taille des points = les nuits tropicales de 2026, la couleur = l'écart à la normale."
)

safe_plot(plot_carte_france, pano, theme)

n_record_nt = int((pano["nt_rang"] == 1).sum())
top3 = pano.head(3)
st.markdown(
    f"Partout **+4 à +6 °C** au-dessus de la normale, et **{n_record_nt} villes sur {len(pano)}** "
    f"battent aussi leur record de nuits tropicales. Les plus fortes anomalies : "
    f"**{top3.iloc[0]['ville']}** (+{top3.iloc[0]['anomalie_tmax']:.1f} °C), "
    f"**{top3.iloc[1]['ville']}** (+{top3.iloc[1]['anomalie_tmax']:.1f} °C), "
    f"**{top3.iloc[2]['ville']}** (+{top3.iloc[2]['anomalie_tmax']:.1f} °C)."
)

with st.expander("📊 Voir le détail ville par ville"):
    safe_plot(plot_panorama, pano, theme)
    st.dataframe(
        pano.rename(columns={
            "ville": "Ville", "anomalie_tmax": "Écart °C", "nt_2026": "Nuits trop. 2026",
            "nt_normale": "Normale", "tmax_rang": "Rang chaleur", "nt_rang": "Rang nuits",
        })[["Ville", "Écart °C", "Nuits trop. 2026", "Normale", "Rang chaleur", "Rang nuits"]],
        use_container_width=True, hide_index=True,
    )

st.divider()

# ─────────────────────────────────────────
# SECTION 4 : ACCIDENT OU TENDANCE ?
# ─────────────────────────────────────────
st.markdown("## 📈 Un pic isolé, ou une tendance de fond ?")

st.markdown(
    "La vraie question honnête : 2026 est-il un accident, ou le sommet d'une pente ? "
    "À l'échelle nationale comme à Lyon, la réponse est la même."
)

safe_plot(plot_france_trend, france, theme)

col_a, col_b = st.columns(2)
with col_a:
    safe_plot(plot_tendance, ete, VILLE_REF, "tmax_moy",
              "Chaleur estivale à Lyon : la pente de fond", theme)
with col_b:
    safe_plot(plot_distribution_decennies, lyon, theme)

pente_tmax = tendance_par_decennie(
    ete[ete["ville"] == VILLE_REF]["year"], ete[ete["ville"] == VILLE_REF]["tmax_moy"]
)
st.markdown(
    f"La chaleur estivale à Lyon grimpe de **{pente_tmax:+.2f} °C par décennie**. Décennie après "
    "décennie, toute la distribution glisse vers le haut : ce n'est pas seulement les records qui "
    "montent, c'est le « normal » lui-même qui devient ce qui était exceptionnel avant. 2026 est le "
    "sommet, pas l'exception."
)

with st.expander("🔬 Creuser : cette tendance est-elle statistiquement solide ?"):
    gL = ete[ete["ville"] == VILLE_REF].set_index("year")
    ic_tmax = tendance_ic(gL.index, gL["tmax_moy"])
    ic_nuits = tendance_ic(gL.index, gL["nuits_trop"])
    ic_fr = tendance_ic(france["year"], france["tmax_moy"])

    st.markdown(
        "Une pente qui monte ne suffit pas : encore faut-il qu'elle soit **distinguable du hasard**. "
        "On mesure donc chaque tendance avec son **intervalle de confiance à 95 %** (régression OLS). "
        "Si l'intervalle ne contient pas zéro, la tendance est statistiquement significative."
    )
    t1, t2, t3 = st.columns(3)
    t1.metric("Chaleur max · Lyon", f"{ic_tmax['pente_dec']:+.2f} °C/déc.",
              f"IC95 : [{ic_tmax['lo']:+.2f} ; {ic_tmax['hi']:+.2f}]")
    t2.metric("Nuits tropicales · Lyon", f"{ic_nuits['pente_dec']:+.1f} /déc.",
              f"IC95 : [{ic_nuits['lo']:+.1f} ; {ic_nuits['hi']:+.1f}]")
    t3.metric("Chaleur max · France (11 villes)", f"{ic_fr['pente_dec']:+.2f} °C/déc.",
              f"IC95 : [{ic_fr['lo']:+.2f} ; {ic_fr['hi']:+.2f}]")

    tous_signif = ic_tmax["significatif"] and ic_nuits["significatif"] and ic_fr["significatif"]
    if tous_signif:
        st.success(
            "Les trois intervalles excluent zéro : le réchauffement estival est **statistiquement "
            "significatif** (95 %), à Lyon comme à l'échelle des 11 villes. La pente n'est pas un "
            "artefact visuel.",
            icon="✅",
        )
    st.caption(
        "Méthode : pente OLS sur les moyennes d'été annuelles, erreur-type analytique, "
        f"n = {ic_tmax['n']} étés (1950-2026). L'IC porte sur la pente, pas sur une année isolée."
    )

st.divider()

# ─────────────────────────────────────────
# SECTION 5 : MÉTHODE, ROBUSTESSE & HONNÊTETÉ
# ─────────────────────────────────────────
st.markdown("## 🔬 Pour ceux qui veulent la preuve")
st.markdown(
    "Un beau graphique ne prouve rien tout seul. Voici les tests que j'ai passés à la donnée avant "
    "d'oser le titre — et, surtout, ce qu'elle **ne** permet **pas** de dire."
)

tab_meth, tab_ref, tab_seuil, tab_dire = st.tabs(
    ["📐 Méthode", "🗓️ Autre période de référence ?", "🌡️ Autre seuil de nuit ?", "✅ Ce qu'on peut affirmer"]
)

with tab_meth:
    st.markdown("""
- **Source** : API archive [Open-Meteo](https://open-meteo.com), basée sur la réanalyse **ERA5**
  (ECMWF), journalier depuis 1950. Gratuite, reproductible, une seule source cohérente pour toutes
  les années — ce qui évite les biais de changement de station.
- **Comparaison équitable** : tous les indicateurs d'été sont calculés sur la **même fenêtre
  calendaire (1er juin → 17 août)**, pour que 2026 (arrêté au 17 août) soit comparable aux étés
  complets du passé. 2026 reste n°1 même ainsi.
- **Normale** : moyenne **1991-2020**, la période de référence de Météo-France.
- **Nuit tropicale** : nuit avec Tmin ≥ 20 °C (définition standard).
- **Limite assumée** : ERA5 est une réanalyse (modèle + observations), pas un thermomètre de rue.
  Les valeurs absolues peuvent différer d'une station locale de quelques dixièmes ; les **écarts et
  tendances**, eux, sont robustes. Le seuil « 35 °C » est un indicateur de journée très chaude, pas
  la définition officielle de canicule (qui dépend de seuils Tmin/Tmax par département).
""")

with tab_ref:
    st.markdown(
        "La « normale » 1991-2020 est un choix. Un sceptique dirait : *« et si tu avais pris une autre "
        "période ? »*. Alors comparons l'écart de la chaleur max de Lyon en 2026 selon **trois** "
        "références classiques :"
    )
    sens = anomalie_multi_ref(ete[ete["ville"] == VILLE_REF].set_index("year")["tmax_moy"])
    st.dataframe(
        sens.rename(columns={"reference": "Période de référence", "normale": "Normale (°C)",
                             "anomalie": "Écart de 2026 (°C)"}),
        use_container_width=True, hide_index=True,
    )
    st.info(
        "Quelle que soit la référence, 2026 ressort **nettement au-dessus** — l'écart grandit même "
        "avec des références plus anciennes. La conclusion ne dépend pas du choix de la fenêtre.",
        icon="🗓️",
    )

with tab_seuil:
    st.markdown(
        "« Nuit tropicale = Tmin ≥ 20 °C » est la définition standard, mais elle aussi est un seuil. "
        "Recalculons les nuits chaudes de Lyon à **18, 20 et 22 °C** — le record de 2026 tient-il ?"
    )
    seuils = nuits_seuils_lyon(lyon)
    st.dataframe(
        seuils.rename(columns={"seuil": "Seuil Tmin", "nt_2026": "Nuits en 2026",
                               "normale": "Normale 1991-2020", "rang": "Rang de 2026",
                               "n_annees": "Étés comparés"}),
        use_container_width=True, hide_index=True,
    )
    st.info(
        "À chaque seuil, 2026 est **n°1 depuis 1950**. Le signal n'est pas un effet de bord d'une "
        "définition : il est robuste au choix du seuil.",
        icon="🌡️",
    )

with tab_dire:
    st.markdown("""
Séparer proprement ce qui est **mesuré**, ce qui est **inféré** et ce qui reste **interprétation**,
c'est la différence entre un dashboard et un travail honnête.

**✅ Ce que la donnée montre (faits mesurés)**
- L'été 2026 est le plus chaud depuis 1950 sur les 11 villes suivies, sur une fenêtre comparable.
- Les nuits tropicales de 2026 battent leur record partout, et le rang tient à plusieurs seuils.
- La tendance de fond au réchauffement estival est statistiquement significative (IC95 excluant zéro).

**🔎 Ce que l'on infère raisonnablement (au-delà de la seule mesure)**
- 2026 s'inscrit dans une tendance, pas dans un accident isolé : c'est le sommet d'une pente.
- Le glissement de toute la distribution suggère que l'« exceptionnel » d'hier devient la norme.

**⛔ Ce que la donnée ne dit PAS ici**
- Elle ne « prouve » pas à elle seule la cause du réchauffement : l'attribution au forçage humain
  relève des études de détection-attribution du GIEC, pas de ces 11 séries.
- « Les 11 villes » n'est pas « la France entière » : c'est un échantillon de grandes villes, pas une
  moyenne surfacique nationale.
- ERA5 n'est pas un thermomètre de rue : on lit des **écarts et tendances**, pas des dixièmes absolus.
""")

st.divider()

# ─────────────────────────────────────────
# SECTION 6 : LE PONT VERS LE CHAPITRE 2 (projet ICU)
# ─────────────────────────────────────────
st.markdown("## 🏘️ Et dans la ville, ça se joue rue par rue")

st.markdown(
    "Si la nuit ne rafraîchit plus, tout le monde n'est pas logé à la même enseigne : à quelques "
    "centaines de mètres près, un quartier dense peut rester bien plus chaud qu'un parc voisin. "
    "C'est le sujet du chapitre 2, à l'échelle de l'îlot à Lyon :"
)
st.markdown(f"👉 **[Îlot de chaleur urbain à Lyon — le détail au grain fin]({ICU_URL})**")

st.divider()

# ─────────────────────────────────────────
# APPEL À L'ACTION
# ─────────────────────────────────────────
cta_left, cta_right = st.columns([3, 2])
with cta_left:
    st.markdown("""
### 👋 On continue ailleurs ?
Je suis **Badreddine**, ingénieur en mathématiques appliquées à Lyon. Je prends des questions du
quotidien et je les tranche avec de la donnée, proprement.
""")
with cta_right:
    st.markdown(
        "🌐 **[badreddineek.com](https://badreddineek.com)**\n\n"
        "🧑‍💻 **[Mon portfolio](https://portfolio.badreddineek.com)**"
    )

st.divider()
st.caption(
    "🌡️ Analyse — Données : Open-Meteo (réanalyse ERA5), 1950-2026 · "
    "Fenêtre comparable 1er juin → 17 août · Normale 1991-2020."
)
