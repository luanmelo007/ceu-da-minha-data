import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import pandas as pd
import io
import requests
from datetime import datetime, date, time as dtime

# ─── Configuração da Página ────────────────────────────────────────────────────

st.set_page_config(
    page_title="🌌 Céu da Minha Data",
    page_icon="🌌",
    layout="centered"
)

st.markdown("""
<style>
    .block-container { max-width: 760px; }
    h1 { text-align: center; }
    .stButton > button { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

st.title("🌌 Céu da Minha Data")
st.markdown(
    "<p style='text-align:center;color:gray;margin-top:-12px'>"
    "Mapa estelar gratuito e personalizado para qualquer momento e lugar"
    "</p>",
    unsafe_allow_html=True
)

# ─── Catálogo de Estrelas ─────────────────────────────────────────────────────

@st.cache_data(show_spinner="🌠 Carregando catálogo de estrelas...")
def load_stars():
    """
    Lê o catálogo estelar do arquivo local stars.csv (gerado pelo download_stars.py).
    Fonte: HYG Database v3 — domínio público.
    """
    import os
    if not os.path.exists("stars.csv"):
        st.error(
            "⚠️ Arquivo `stars.csv` não encontrado!\n\n"
            "Execute no terminal: `python download_stars.py`"
        )
        st.stop()
    df = pd.read_csv("stars.csv")
    return df[df["mag"] <= 7.5].reset_index(drop=True)

# ─── Geocodificação ───────────────────────────────────────────────────────────

def geocode_city(city_name: str):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city_name, "format": "json", "limit": 1},
            headers={"User-Agent": "CeuDaMinhaData/1.0 (streamlit-app)"},
            timeout=10,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except Exception:
        pass
    return None, None, None

# ─── Temas visuais ────────────────────────────────────────────────────────────

THEMES = {
    "🌌 Escuro Clássico": dict(
        bg="#06061f", sky="#0b0b35", star="white",
        grid="#1a1a50", border="#5050b0", text="white", compass="#8888cc"
    ),
    "🌊 Azul Profundo": dict(
        bg="#010d1f", sky="#021840", star="#d8eeff",
        grid="#062a6a", border="#1a5ccc", text="#b0d0f8", compass="#5590e0"
    ),
    "☀️ Claro Minimalista": dict(
        bg="#f0f0f8", sky="#e4e4f4", star="#12124a",
        grid="#b8b8d8", border="#5050a0", text="#1a1a5e", compass="#7070b0"
    ),
    "✨ Preto & Dourado": dict(
        bg="#080600", sky="#100d00", star="#ffd700",
        grid="#201800", border="#806000", text="#ffd700", compass="#c09000"
    ),
    "🌹 Rosé Romântico": dict(
        bg="#1a0a10", sky="#280f18", star="#ffd0e0",
        grid="#401525", border="#b04060", text="#ffd0e0", compass="#e08888"
    ),
    "🟢 Verde Hacker": dict(
        bg="#000a00", sky="#001400", star="#00ff88",
        grid="#003300", border="#007700", text="#00ff88", compass="#00cc66"
    ),
}

# ─── Geração do Mapa ─────────────────────────────────────────────────────────

def make_star_map(lat: float, lon: float, dt_utc: datetime,
                  title: str, subtitle: str, theme_name: str,
                  mag_limit: float) -> plt.Figure:
    from astropy.coordinates import SkyCoord, EarthLocation, AltAz
    from astropy.time import Time
    import astropy.units as u

    # Carrega e filtra estrelas
    stars = load_stars()
    stars = stars[stars["mag"] <= mag_limit].copy()

    # Configura observador
    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=0 * u.m)
    t = Time(dt_utc)
    frame = AltAz(obstime=t, location=location)

    # Converte coordenadas equatoriais → horizontais
    coords = SkyCoord(ra=stars["ra"].values * u.hour,
                      dec=stars["dec"].values * u.deg)
    altaz = coords.transform_to(frame)

    alt = altaz.alt.deg
    az  = altaz.az.deg
    mag = stars["mag"].values

    # Apenas estrelas acima do horizonte
    vis = alt > 0
    alt, az, mag = alt[vis], az[vis], mag[vis]

    # Projeção estereográfica zenital
    # centro = zênite, borda = horizonte (r=1)
    r = np.cos(np.radians(alt))
    x =  r * np.sin(np.radians(az))   # Leste → direita
    y =  r * np.cos(np.radians(az))   # Norte → cima

    # Tamanho dos pontos proporcional ao brilho (mag menor = mais brilhante)
    sizes = np.clip(5.5 - mag, 0.15, 5.0) ** 2 * 2.8

    c = THEMES[theme_name]

    # ── Figure ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(8, 10.5), facecolor=c["bg"])
    ax  = fig.add_axes([0.08, 0.11, 0.84, 0.72])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.18, 1.18)
    ax.set_ylim(-1.18, 1.18)

    theta = np.linspace(0, 2 * np.pi, 360)

    # Fundo do céu (círculo)
    ax.fill(np.cos(theta), np.sin(theta), color=c["sky"], zorder=0)

    # Anéis de altitude (30° e 60°)
    for alt_deg in [30, 60]:
        rc = np.cos(np.radians(alt_deg))
        ax.plot(rc * np.cos(theta), rc * np.sin(theta),
                color=c["grid"], lw=0.5, alpha=0.45, zorder=1, ls="--")

    # Linhas de azimute a cada 30°
    for az_d in range(0, 360, 30):
        ar = np.radians(az_d)
        ax.plot([0, np.sin(ar)], [0, np.cos(ar)],
                color=c["grid"], lw=0.3, alpha=0.3, zorder=1)

    # Pontos ponto central (zênite)
    ax.scatter([0], [0], s=6, c=c["grid"], zorder=2, alpha=0.5)

    # Estrelas
    sc = ax.scatter(x, y, s=sizes, c=c["star"], zorder=3,
                    linewidths=0, alpha=0.96)

    # Clipping circular
    clip = Circle((0, 0), 1.0, transform=ax.transData)
    sc.set_clip_path(clip)

    # Borda do círculo
    ax.add_patch(Circle((0, 0), 1.0, fill=False,
                         edgecolor=c["border"], lw=2.2, zorder=5))

    # Pontos cardeais  (N/S/L/O)
    cardinal = {"N": (0, 1), "L": (1, 0), "S": (0, -1), "O": (-1, 0)}
    for lbl, (cx, cy) in cardinal.items():
        ax.text(cx * 1.09, cy * 1.09, lbl,
                color=c["compass"], fontsize=11, ha="center", va="center",
                fontweight="bold", zorder=6)

    # ── Textos ────────────────────────────────────────────────────────────────
    # Título
    fig.text(0.5, 0.905, title,
             color=c["text"], fontsize=15, ha="center",
             fontweight="bold", fontfamily="serif")

    # Subtítulo
    if subtitle.strip():
        fig.text(0.5, 0.873, subtitle,
                 color=c["text"], fontsize=9, ha="center", alpha=0.75)

    # Linha separadora decorativa
    line_y = 0.862 if subtitle.strip() else 0.885
    fig.add_artist(plt.Line2D([0.2, 0.8], [line_y - 0.008, line_y - 0.008],
                               transform=fig.transFigure,
                               color=c["border"], lw=0.8, alpha=0.5))

    # Rodapé: coordenadas + data/hora
    fig.text(
        0.5, 0.065,
        f"Lat {lat:+.4f}°   Lon {lon:+.4f}°   ·   "
        f"{dt_utc.strftime('%d/%m/%Y  %H:%M')} UTC",
        color=c["text"], fontsize=7, ha="center", alpha=0.45
    )
    fig.text(
        0.5, 0.038,
        f"{len(alt):,} estrelas visíveis  ·  magnitude ≤ {mag_limit}  ·  "
        f"HYG Database / Astropy",
        color=c["text"], fontsize=6.5, ha="center", alpha=0.35
    )

    return fig

# ─── Sidebar de Configurações ─────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configurações")

    # ── Localização ──────────────────────────────────────────────────────────
    st.subheader("📍 Localização")
    loc_mode = st.radio(
        "Modo de entrada",
        ["🔍 Buscar cidade", "🗺️ Lat/Lon manual"],
        label_visibility="collapsed"
    )

    # Padrão: Sobral, CE
    lat_default, lon_default = -3.6880, -40.3497

    if loc_mode == "🔍 Buscar cidade":
        city_input = st.text_input("Nome da cidade", value="Sobral, Ceará, Brasil",
                                   placeholder="Ex: São Paulo, Rio de Janeiro...")
        if st.button("🔍 Buscar coordenadas"):
            with st.spinner("Buscando..."):
                la, lo, display = geocode_city(city_input)
            if la is not None:
                st.session_state["lat"] = la
                st.session_state["lon"] = lo
                st.success(f"✅ {display[:70]}")
            else:
                st.error("❌ Cidade não encontrada. Tente ser mais específico.")

        lat = st.session_state.get("lat", lat_default)
        lon = st.session_state.get("lon", lon_default)
        st.caption(f"📌 Lat {lat:.4f}° · Lon {lon:.4f}°")

    else:
        lat = st.number_input("Latitude", value=lat_default,
                               min_value=-90.0, max_value=90.0, format="%.4f")
        lon = st.number_input("Longitude", value=lon_default,
                               min_value=-180.0, max_value=180.0, format="%.4f")

    st.divider()

    # ── Data e Hora ──────────────────────────────────────────────────────────
    st.subheader("📅 Data e Hora")

    tz_offset = st.selectbox(
        "Fuso horário",
        options=[-5, -4, -3, -2, 0, 1, 2, 3],
        index=2,
        format_func=lambda x: f"UTC{x:+d}  {'(Brasília/Fortaleza)' if x==-3 else '(Acre)' if x==-5 else '(Manaus)' if x==-4 else '(Fernando de Noronha)' if x==-2 else '(UTC)' if x==0 else ''}",
        help="Horário de Brasília = UTC-3 | Fortaleza = UTC-3 | Manaus = UTC-4"
    )

    col1, col2 = st.columns(2)
    with col1:
        input_date = st.date_input("Data", value=date.today())
    with col2:
        input_time = st.time_input("Hora (local)", value=dtime(22, 0))

    # Converte para UTC
    local_dt = datetime.combine(input_date, input_time)
    from datetime import timedelta
    dt_utc = local_dt - timedelta(hours=tz_offset)
    st.caption(f"🕐 {local_dt.strftime('%d/%m/%Y %H:%M')} local → "
               f"{dt_utc.strftime('%H:%M')} UTC")

    st.divider()

    # ── Personalização ───────────────────────────────────────────────────────
    st.subheader("✏️ Personalização")

    title    = st.text_input("Título", value="O Céu Naquele Dia",
                              max_chars=60)
    subtitle = st.text_input("Subtítulo", value="Um momento especial sob as estrelas",
                              max_chars=80)
    theme    = st.selectbox("Tema de cores", list(THEMES.keys()))
    mag_limit = st.slider(
        "Quantidade de estrelas (magnitude limite)",
        min_value=2.0, max_value=7.0, value=5.5, step=0.5,
        help="Valores maiores = mais estrelas (incluindo as mais fracas)"
    )

# ─── Botão principal e resultado ──────────────────────────────────────────────

st.divider()

gerar = st.button("🌌 Gerar Mapa Estelar", type="primary", use_container_width=True)

if gerar:
    with st.spinner("✨ Calculando posições das estrelas..."):
        try:
            fig = make_star_map(lat, lon, dt_utc, title, subtitle, theme, mag_limit)

            # Salva em buffer para exibição e download
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200,
                        bbox_inches="tight", facecolor=fig.get_facecolor())
            buf.seek(0)

            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.download_button(
                label="⬇️ Baixar PNG em alta qualidade",
                data=buf,
                file_name=f"ceu_{input_date.strftime('%Y%m%d')}.png",
                mime="image/png",
                use_container_width=True,
            )
            st.success("Mapa gerado com sucesso! Clique em Baixar para salvar.")

        except ImportError:
            st.error(
                "⚠️ Biblioteca `astropy` não encontrada.\n\n"
                "Execute no terminal: `pip install astropy`"
            )
        except Exception as e:
            st.error(f"Erro ao gerar mapa: {e}")
            st.exception(e)

# ─── Rodapé ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<p style='text-align:center; font-size:11px; color:gray'>
Dados estelares: <a href='https://github.com/astronexus/HYG-Database' target='_blank'>HYG Database</a> (David Nash, domínio público) · 
Cálculos astronômicos: <a href='https://www.astropy.org' target='_blank'>Astropy</a> ·
Geocodificação: <a href='https://nominatim.openstreetmap.org' target='_blank'>OpenStreetMap Nominatim</a>
</p>
""", unsafe_allow_html=True)