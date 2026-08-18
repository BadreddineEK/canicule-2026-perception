"""
Visualisations Plotly pour le dashboard canicule.
Charte centralisée, thème clair par défaut.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

COLOR_2026 = "#C0392B"     # rouge profond : l'année en cours
COLOR_BAR = "#F0B27A"      # orange doux : les autres années
COLOR_NORMALE = "#2C3E50"  # ligne de repère (normale)
COLOR_COOL = "#3498DB"


def _palette(theme: str) -> dict:
    if theme == "light":
        return dict(bg="#ffffff", font="#1a1d24", grid="rgba(0,0,0,0.10)", ref="rgba(0,0,0,0.55)")
    return dict(bg="#0e1117", font="#fafafa", grid="rgba(255,255,255,0.10)", ref="rgba(255,255,255,0.55)")


def _apply_theme(fig: go.Figure, height: int, theme: str) -> go.Figure:
    p = _palette(theme)
    fig.update_layout(
        plot_bgcolor=p["bg"], paper_bgcolor=p["bg"],
        font=dict(color=p["font"], size=13), title_font=dict(size=16),
        height=height, margin=dict(l=10, r=10, t=70, b=10),
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(gridcolor=p["grid"], zerolinecolor=p["grid"])
    fig.update_yaxes(gridcolor=p["grid"], zerolinecolor=p["grid"])
    return fig


@st.cache_data(show_spinner=False)
def plot_nuits_tropicales(ete: pd.DataFrame, ville: str = "Lyon", theme: str = "light") -> go.Figure:
    """Barres du nombre de nuits tropicales par année, l'année en cours en évidence."""
    p = _palette(theme)
    g = ete[ete["ville"] == ville].sort_values("year")
    norm = float(g[(g["year"] >= 1991) & (g["year"] <= 2020)]["nuits_trop"].mean())
    colors = [COLOR_2026 if y == 2026 else COLOR_BAR for y in g["year"]]

    fig = go.Figure(go.Bar(
        x=g["year"], y=g["nuits_trop"], marker_color=colors,
        hovertemplate="%{x}<br>%{y} nuits tropicales<extra></extra>",
    ))
    fig.add_hline(
        y=norm, line_dash="dash", line_color=COLOR_NORMALE,
        annotation_text=f"Normale 1991-2020 : {norm:.0f} nuits",
        annotation_position="top left",
    )
    fig.update_layout(
        title=f"Nuits tropicales à {ville} (Tmin ≥ 20 °C) — 1er juin au 17 août",
        xaxis_title=None, yaxis_title="Nombre de nuits",
    )
    return _apply_theme(fig, height=430, theme=theme)


@st.cache_data(show_spinner=False)
def plot_panorama(pano: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Écart de température de l'été 2026 vs normale, par ville."""
    d = pano.sort_values("anomalie_tmax", ascending=True)
    fig = go.Figure(go.Bar(
        x=d["anomalie_tmax"], y=d["ville"], orientation="h",
        marker=dict(color=d["anomalie_tmax"], colorscale="OrRd", cmin=0),
        text=[f"+{v:.1f} °C" for v in d["anomalie_tmax"]],
        textposition="outside",
        hovertemplate="%{y}<br>+%{x:.1f} °C vs normale<extra></extra>",
    ))
    fig.update_layout(
        title="Été 2026 vs normale 1991-2020 — écart de température max moyenne",
        xaxis_title="Écart à la normale (°C)", yaxis_title=None,
        xaxis=dict(range=[0, d["anomalie_tmax"].max() + 1.2]),
    )
    return _apply_theme(fig, height=440, theme=theme)


@st.cache_data(show_spinner=False)
def plot_distribution_decennies(lyon_jour: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Distribution des Tmax estivales de Lyon, décennie par décennie (le glissement)."""
    p = _palette(theme)
    s = lyon_jour[lyon_jour["month"].isin([6, 7, 8])].copy()
    s["dec"] = (s["year"] // 10 * 10).astype(int)
    s = s[s["dec"] >= 1950]
    decs = sorted(s["dec"].unique())
    means = s.groupby("dec")["tmax"].mean()
    vmin, vmax = means.min(), means.max()

    fig = go.Figure()
    for dc in decs:
        vals = s[s["dec"] == dc]["tmax"]
        t = (means[dc] - vmin) / (vmax - vmin + 1e-9)
        color = f"rgba({int(80 + 175 * t)}, {int(120 - 90 * t)}, {int(200 - 170 * t)}, 0.85)"
        fig.add_trace(go.Box(
            y=vals, name=f"{dc}s", marker_color=color,
            boxpoints=False, line_width=1.4,
        ))
    fig.update_layout(
        title="Températures max estivales à Lyon, décennie par décennie",
        yaxis_title="Température max journalière (°C)", xaxis_title=None,
        showlegend=False,
    )
    return _apply_theme(fig, height=440, theme=theme)


@st.cache_data(show_spinner=False)
def plot_tendance(ete: pd.DataFrame, ville: str = "Lyon", col: str = "tmax_moy",
                  titre: str = "", theme: str = "light") -> go.Figure:
    """Nuage annuel + droite de tendance, avec la pente par décennie annotée."""
    p = _palette(theme)
    g = ete[ete["ville"] == ville].sort_values("year")
    x, y = g["year"].values, g[col].values
    a, b = np.polyfit(x, y, 1)
    trend = a * x + b
    colors = [COLOR_2026 if yr == 2026 else COLOR_COOL for yr in x]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers", marker=dict(size=7, color=colors),
        name="Étés", hovertemplate="%{x}<br>%{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=trend, mode="lines", line=dict(color=COLOR_2026, width=2),
        name="Tendance",
    ))
    fig.add_annotation(
        x=x[2], y=trend[2], xanchor="left", yanchor="bottom",
        text=f"+{a*10:.2f} °C / décennie", showarrow=False,
        font=dict(color=COLOR_2026, size=13),
    )
    fig.update_layout(
        title=titre or f"Tendance de la chaleur estivale à {ville}",
        xaxis_title=None, yaxis_title="Température max moyenne (°C)",
        showlegend=False,
    )
    return _apply_theme(fig, height=400, theme=theme)


@st.cache_data(show_spinner=False)
def plot_carte_france(pano: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Carte de France : chaque ville, taille = nuits tropicales 2026, couleur = écart à la normale."""
    p = _palette(theme)
    map_style = "carto-positron" if theme == "light" else "carto-darkmatter"
    d = pano.dropna(subset=["lat", "lon"])

    fig = go.Figure(go.Scattermapbox(
        lat=d["lat"], lon=d["lon"], mode="markers+text",
        marker=dict(
            size=d["nt_2026"] / 2 + 9,
            color=d["anomalie_tmax"], colorscale="OrRd", cmin=3,
            colorbar=dict(title="Écart<br>°C"),
            opacity=0.9,
        ),
        text=d["ville"], textposition="top center", textfont=dict(size=11, color=p["font"]),
        customdata=d[["anomalie_tmax", "nt_2026", "nt_normale"]],
        hovertemplate=("<b>%{text}</b><br>+%{customdata[0]:.1f} °C vs normale<br>"
                       "%{customdata[1]} nuits tropicales (normale %{customdata[2]:.0f})<extra></extra>"),
    ))
    fig.update_layout(
        title="Été 2026 en France — écart à la normale et nuits tropicales",
        mapbox=dict(style=map_style, center=dict(lat=46.6, lon=2.6), zoom=4.5),
        height=560, margin=dict(l=10, r=10, t=70, b=10),
        paper_bgcolor=p["bg"], font=dict(color=p["font"], size=13), title_font=dict(size=16),
        hoverlabel=dict(font_size=13),
    )
    return fig


@st.cache_data(show_spinner=False)
def plot_france_trend(france: pd.DataFrame, theme: str = "light") -> go.Figure:
    """Nuits tropicales moyennes des 11 villes, année par année : la vue France entière."""
    g = france.sort_values("year")
    norm = float(g[(g["year"] >= 1991) & (g["year"] <= 2020)]["nuits_trop"].mean())
    colors = [COLOR_2026 if y == 2026 else COLOR_BAR for y in g["year"]]

    fig = go.Figure(go.Bar(
        x=g["year"], y=g["nuits_trop"], marker_color=colors,
        hovertemplate="%{x}<br>%{y:.1f} nuits (moyenne 11 villes)<extra></extra>",
    ))
    fig.add_hline(
        y=norm, line_dash="dash", line_color=COLOR_NORMALE,
        annotation_text=f"Normale 1991-2020 : {norm:.0f}", annotation_position="top left",
    )
    fig.update_layout(
        title="Nuits tropicales en France (moyenne de 11 grandes villes)",
        xaxis_title=None, yaxis_title="Nombre de nuits",
    )
    return _apply_theme(fig, height=400, theme=theme)
