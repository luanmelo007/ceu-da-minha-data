import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd
import io, requests
from datetime import datetime, date, time as dtime, timedelta

st.set_page_config(page_title="🌌 Céu da Minha Data", page_icon="🌌", layout="centered")
st.markdown("""<style>.block-container{max-width:760px}h1{text-align:center}</style>""",
            unsafe_allow_html=True)
st.title("🌌 Céu da Minha Data")
st.markdown("<p style='text-align:center;color:gray;margin-top:-12px'>"
            "Mapa estelar personalizado · estilo pôster</p>", unsafe_allow_html=True)

# ─── Utilitários ─────────────────────────────────────────────────────────────
MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

def fmt_data_pt(dt):
    return f"{dt.day} de {MESES[dt.month-1]} de {dt.year}"

def dd_to_dm(deg, is_lat):
    d = int(abs(deg)); m = round((abs(deg)-d)*60)
    s = ("N" if deg>=0 else "S") if is_lat else ("L" if deg>=0 else "W")
    return f"{d}°{m:02d}'{s}"

# ─── Nomes PT ─────────────────────────────────────────────────────────────────
CONST_PT = {
    "And":"Andrômeda",    "Aps":"Ave do Paraíso", "Aqr":"Aquário",
    "Aql":"Águia",        "Ara":"Altar",           "Ari":"Áries",
    "Aur":"Cocheiro",     "Boo":"Boieiro",         "Cae":"Cinzel",
    "Cam":"Girafa",       "Cnc":"Câncer",          "CVn":"Cães de Caça",
    "CMa":"Cão Maior",    "CMi":"Cão Menor",       "Cap":"Capricórnio",
    "Car":"Quilha",       "Cas":"Cassiopeia",      "Cen":"Centauro",
    "Cep":"Cefeu",        "Cet":"Baleia",          "Cha":"Camaleão",
    "Cir":"Compasso",     "Col":"Pomba",           "Com":"Cab. Berenice",
    "CrA":"Coroa Austral","CrB":"Coroa Boreal",    "Crv":"Corvo",
    "Crt":"Taça",         "Cru":"Cruzeiro do Sul", "Cyg":"Cisne",
    "Del":"Golfinho",     "Dor":"Dourado",         "Dra":"Dragão",
    "Equ":"Potro",        "Eri":"Erídano",         "For":"Fornalha",
    "Gem":"Gêmeos",       "Gru":"Grou",            "Her":"Hércules",
    "Hor":"Relógio",      "Hya":"Hidra",           "Hyi":"Hidra Macho",
    "Ind":"Índio",        "Lac":"Lagartixa",       "Leo":"Leão",
    "LMi":"Leão Menor",   "Lep":"Lebre",           "Lib":"Balança",
    "Lup":"Lobo",         "Lyn":"Lince",           "Lyr":"Lira",
    "Men":"Mesa",         "Mic":"Microscópio",     "Mon":"Unicórnio",
    "Mus":"Mosca",        "Nor":"Esquadro",        "Oct":"Oitante",
    "Oph":"Ofiúco",       "Ori":"Órion",           "Pav":"Pavão",
    "Peg":"Pégaso",       "Per":"Perseu",          "Phe":"Fênix",
    "Pic":"Pintor",       "PsA":"Peixe Austral",   "Psc":"Peixes",
    "Pup":"Popa",         "Pyx":"Bússola",         "Ret":"Retículo",
    "Sge":"Flecha",       "Sgr":"Sagitário",       "Sco":"Escorpião",
    "Scl":"Escultor",     "Sct":"Escudo",          "Ser":"Serpente",
    "Sex":"Sextante",     "Tau":"Touro",           "Tel":"Telescópio",
    "TrA":"Triâng. Austral","Tri":"Triângulo",     "Tuc":"Tucano",
    "UMa":"Ursa Maior",   "UMi":"Ursa Menor",      "Vel":"Vela",
    "Vir":"Virgem",       "Vol":"Peixe Voador",    "Vul":"Raposa",
}

# ─── Temas ────────────────────────────────────────────────────────────────────
THEMES = {
    "🎨 Poster Clássico": dict(
        bg="#0c1022", sky="#0c1022", star="white", star_alpha=0.95,
        line="#8090c0", line_alpha=0.75, line_w=0.9,
        name="#90a0cc", border="#3a4478", title="white", meta="#7a89b8"),
    "🌌 Escuro Azulado": dict(
        bg="#06061f", sky="#0b0b35", star="white", star_alpha=0.95,
        line="#6878cc", line_alpha=0.75, line_w=0.9,
        name="#8898dd", border="#5050b0", title="white", meta="#8888cc"),
    "☀️ Claro Minimalista": dict(
        bg="#f2f2f8", sky="#e8e8f4", star="#12124a", star_alpha=0.9,
        line="#4455a8", line_alpha=0.65, line_w=0.9,
        name="#3344a0", border="#aaaacc", title="#12124a", meta="#5555a0"),
    "✨ Preto & Dourado": dict(
        bg="#080600", sky="#100d00", star="#ffd700", star_alpha=0.9,
        line="#c09020", line_alpha=0.75, line_w=0.9,
        name="#d4a820", border="#806000", title="#ffd700", meta="#907000"),
    "🌹 Rosé Romântico": dict(
        bg="#1a0a10", sky="#240e16", star="#ffd0e0", star_alpha=0.9,
        line="#d06888", line_alpha=0.75, line_w=0.9,
        name="#e080a0", border="#b04060", title="#ffd0e0", meta="#c07090"),
}

# ─── Carregamento de dados ────────────────────────────────────────────────────
@st.cache_data(show_spinner="🌠 Carregando catálogo de estrelas...")
def load_stars():
    import os
    if not os.path.exists("stars.csv"):
        st.error("⚠️ Execute: `python download_stars.py`"); st.stop()
    return pd.read_csv("stars.csv")

@st.cache_data(show_spinner="🔭 Carregando dados de constelações (Stellarium)...")
def load_constellation_hip_pairs():
    """
    Carrega pares HIP das linhas de constelações do Stellarium.
    Formato: <abbr> <n_pares> <hip1a> <hip1b> <hip2a> <hip2b> ...
    """
    url = ("https://raw.githubusercontent.com/Stellarium/stellarium/"
           "v0.21.3/skycultures/western/constellationship.fab")
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        consts = {}
        for line in r.text.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) < 4 or parts[0].startswith('#'):
                continue
            abbr  = parts[0]
            hips  = [int(x) for x in parts[2:]]
            pairs = [(hips[i], hips[i+1]) for i in range(0, len(hips)-1, 2)]
            consts[abbr] = pairs
        return consts
    except Exception as e:
        st.warning(f"Constelações indisponíveis: {e}")
        return {}

def geocode_city(city_name):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": city_name, "format": "json", "limit": 1},
                         headers={"User-Agent": "CeuDaMinhaData/1.0"}, timeout=10)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except Exception:
        pass
    return None, None, None

# ─── Projeção ─────────────────────────────────────────────────────────────────
def project(alt, az):
    """Projeção azimutal equidistante: zênite=centro, horizonte=borda."""
    r = 1.0 - alt / 90.0
    return r * np.sin(np.radians(az)), r * np.cos(np.radians(az))

# ─── Mapa Estelar ─────────────────────────────────────────────────────────────
def make_star_map(lat, lon, dt_utc, local_dt, title, subtitle,
                  theme_name, mag_limit, show_lines, show_names,
                  show_grid, show_compass):
    from astropy.coordinates import SkyCoord, EarthLocation, AltAz
    from astropy.time import Time
    import astropy.units as u

    stars  = load_stars()
    stars  = stars[stars["mag"] <= mag_limit].copy().reset_index(drop=True)

    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=0*u.m)
    t        = Time(dt_utc)
    frame    = AltAz(obstime=t, location=location)

    # ── Posições das estrelas ─────────────────────────────────────────────────
    coords = SkyCoord(ra=stars["ra"].values*u.hour, dec=stars["dec"].values*u.deg)
    altaz  = coords.transform_to(frame)
    s_alt  = altaz.alt.deg
    s_az   = altaz.az.deg
    s_mag  = stars["mag"].values

    vis   = s_alt > 0
    n_vis = vis.sum()
    s_alt, s_az, s_mag = s_alt[vis], s_az[vis], s_mag[vis]
    sx, sy = project(s_alt, s_az)

    c     = THEMES[theme_name]
    theta = np.linspace(0, 2*np.pi, 360)

    # ── Figura ────────────────────────────────────────────────────────────────
    FW, FH = 7.0, 10.0
    fig = plt.figure(figsize=(FW, FH), facecolor=c["bg"])

    AX_W = 0.88
    AX_H = AX_W * FW / FH
    AX_L = (1.0 - AX_W) / 2
    AX_B = 1.0 - AX_H - 0.02

    ax = fig.add_axes([AX_L, AX_B, AX_W, AX_H])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.12, 1.12); ax.set_ylim(-1.12, 1.12)

    # Fundo do céu
    ax.fill(np.cos(theta), np.sin(theta), color=c["sky"], zorder=0)

    # Grade (opcional)
    if show_grid:
        for ad in [30, 60]:
            rc = 1.0 - ad/90.0
            ax.plot(rc*np.cos(theta), rc*np.sin(theta),
                    color=c["line"], lw=0.3, alpha=0.2, zorder=1, ls="--")

    # ── Linhas de constelações via HIP ────────────────────────────────────────
    if show_lines or show_names:
        const_pairs = load_constellation_hip_pairs()

        if const_pairs and "hip" in stars.columns:
            # Lookup HIP → índice em stars (usando todos os stars, não só vis)
            stars_all  = load_stars()
            stars_all  = stars_all[stars_all["mag"] <= mag_limit].copy().reset_index(drop=True)
            hip_col    = stars_all["hip"].fillna(-1).astype(int)
            hip_to_idx = {h: i for i, h in enumerate(hip_col) if h > 0}

            # Calcula AltAz para TODAS as estrelas (não só as visíveis)
            coords_all = SkyCoord(ra=stars_all["ra"].values*u.hour,
                                  dec=stars_all["dec"].values*u.deg)
            altaz_all  = coords_all.transform_to(frame)
            all_alt    = altaz_all.alt.deg
            all_az     = altaz_all.az.deg

            const_centers = {}   # abbr → lista de (x,y) para calcular centróide

            for abbr, pairs in const_pairs.items():
                cx_list, cy_list = [], []
                for h1, h2 in pairs:
                    i1 = hip_to_idx.get(h1, -1)
                    i2 = hip_to_idx.get(h2, -1)
                    if i1 < 0 or i2 < 0:
                        continue
                    alt1, az1 = all_alt[i1], all_az[i1]
                    alt2, az2 = all_alt[i2], all_az[i2]
                    # Ambas as estrelas precisam estar acima do horizonte
                    if alt1 < 5 or alt2 < 5:
                        continue
                    x1, y1 = project(alt1, az1)
                    x2, y2 = project(alt2, az2)
                    if show_lines:
                        # Halo suave
                        ax.plot([x1,x2],[y1,y2], color=c["line"],
                                lw=c["line_w"]*3.5, alpha=c["line_alpha"]*0.15,
                                zorder=2, solid_capstyle="round")
                        # Linha principal
                        ax.plot([x1,x2],[y1,y2], color=c["line"],
                                lw=c["line_w"], alpha=c["line_alpha"],
                                zorder=2, solid_capstyle="round")
                    cx_list.extend([x1,x2])
                    cy_list.extend([y1,y2])

                if cx_list:
                    const_centers[abbr] = (np.mean(cx_list), np.mean(cy_list))

            # Nomes das constelações no centróide
            if show_names:
                for abbr, (cx, cy) in const_centers.items():
                    if cx**2 + cy**2 < 0.90:
                        nome = CONST_PT.get(abbr, abbr)
                        ax.text(cx, cy, nome, color=c["name"],
                                fontsize=6, ha="center", va="center",
                                alpha=0.9, zorder=4, style="italic",
                                fontfamily="serif")

    # ── Estrelas ──────────────────────────────────────────────────────────────
    order  = np.argsort(s_mag)[::-1]
    xo, yo, mo = sx[order], sy[order], s_mag[order]
    sizes = np.clip(6.5 - mo, 0.15, 6.0)**2 * 2.2
    ax.scatter(xo, yo, s=sizes, c=c["star"], zorder=3,
               linewidths=0, alpha=c["star_alpha"])

    # Clip circular
    clip = Circle((0,0), 1.0, transform=ax.transData)
    for a in ax.collections + ax.lines + ax.texts:
        a.set_clip_path(clip)

    # Borda
    ax.add_patch(Circle((0,0), 1.0, fill=False,
                         edgecolor=c["border"], lw=1.0, zorder=5, alpha=0.9))

    # Pontos cardeais (opcional)
    if show_compass:
        for lbl,(cx,cy) in {"N":(0,1),"L":(1,0),"S":(0,-1),"O":(-1,0)}.items():
            ax.text(cx*1.07,cy*1.07, lbl, color=c["meta"],
                    fontsize=9, ha="center", va="center",
                    fontweight="bold", zorder=6, alpha=0.65)

    # ── Textos abaixo do círculo ──────────────────────────────────────────────
    y_line1 = AX_B - 0.022
    fig.add_artist(plt.Line2D([0.15,0.85],[y_line1]*2,
                               transform=fig.transFigure,
                               color=c["border"], lw=0.8, alpha=0.6))

    y_title = y_line1 - 0.09
    fig.text(0.5, y_title, title, color=c["title"], fontsize=26,
             ha="center", va="center", fontweight="bold", fontfamily="serif")

    y_line2 = y_title - 0.075
    fig.add_artist(plt.Line2D([0.30,0.70],[y_line2]*2,
                               transform=fig.transFigure,
                               color=c["border"], lw=0.6, alpha=0.5))

    y_sub = y_line2 - 0.038
    if subtitle.strip():
        fig.text(0.5, y_sub, subtitle, color=c["meta"], fontsize=9.5,
                 ha="center", va="center", style="italic",
                 fontfamily="serif", alpha=0.85)
        y_date = y_sub - 0.048
    else:
        y_date = y_line2 - 0.048

    fig.text(0.5, y_date,
             f"{fmt_data_pt(local_dt)}  ·  {local_dt.strftime('%H:%M')}",
             color=c["meta"], fontsize=9, ha="center", va="center", alpha=0.8)
    fig.text(0.5, y_date - 0.038,
             f"{dd_to_dm(lat,True)}  ·  {dd_to_dm(lon,False)}",
             color=c["meta"], fontsize=8.5, ha="center", va="center", alpha=0.7)

    return fig

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")

    st.subheader("📍 Localização")
    loc_mode = st.radio("Modo", ["🔍 Buscar cidade","🗺️ Lat/Lon manual"],
                        label_visibility="collapsed")
    lat_default, lon_default = -3.6880, -40.3497

    if loc_mode == "🔍 Buscar cidade":
        city_input = st.text_input("Cidade", value="Sobral, Ceará, Brasil")
        if st.button("🔍 Buscar"):
            with st.spinner("Buscando..."):
                la, lo, disp = geocode_city(city_input)
            if la:
                st.session_state["lat"] = la
                st.session_state["lon"] = lo
                st.success(f"✅ {disp[:65]}")
            else:
                st.error("❌ Cidade não encontrada.")
        lat = st.session_state.get("lat", lat_default)
        lon = st.session_state.get("lon", lon_default)
        st.caption(f"📌 {dd_to_dm(lat,True)} · {dd_to_dm(lon,False)}")
    else:
        lat = st.number_input("Latitude",  value=lat_default, format="%.4f")
        lon = st.number_input("Longitude", value=lon_default, format="%.4f")

    st.divider()
    st.subheader("📅 Data e Hora")
    tz_offset = st.selectbox("Fuso horário", [-5,-4,-3,-2,0,1,2,3], index=2,
        format_func=lambda x: f"UTC{x:+d} {'(Brasília/Fortaleza)' if x==-3 else '(Acre)' if x==-5 else '(Manaus)' if x==-4 else '(Fernando de Noronha)' if x==-2 else '(UTC)' if x==0 else ''}")
    col1, col2 = st.columns(2)
    with col1: input_date = st.date_input("Data", value=date.today())
    with col2: input_time = st.time_input("Hora (local)", value=dtime(22, 0))
    local_dt = datetime.combine(input_date, input_time)
    dt_utc   = local_dt - timedelta(hours=tz_offset)
    st.caption(f"🕐 {fmt_data_pt(local_dt)} · {local_dt.strftime('%H:%M')}")

    st.divider()
    st.subheader("✏️ Texto")
    title    = st.text_input("Título", value="O Céu Naquele Dia", max_chars=40)
    subtitle = st.text_input("Subtítulo (opcional)", value="",
                              placeholder="Ex: o dia que o Ray nasceu", max_chars=60)

    st.divider()
    st.subheader("🎨 Visual")
    theme     = st.selectbox("Tema", list(THEMES.keys()))
    mag_limit = st.slider("Quantidade de estrelas", 2.0, 7.0, 5.5, 0.5)

    st.divider()
    st.subheader("🔭 Constelações")
    show_lines = st.toggle("Linhas das constelações", value=True)
    show_names = st.toggle("Nomes das constelações",  value=True)

    st.divider()
    st.subheader("⚙️ Extras")
    show_grid    = st.toggle("Grade de altitude", value=False)
    show_compass = st.toggle("Pontos cardeais",   value=False)

# ─── Geração ──────────────────────────────────────────────────────────────────
st.divider()

if st.button("🌌 Gerar Mapa Estelar", type="primary", use_container_width=True):
    with st.spinner("✨ Gerando mapa..."):
        try:
            fig = make_star_map(lat, lon, dt_utc, local_dt, title, subtitle,
                                theme, mag_limit, show_lines, show_names,
                                show_grid, show_compass)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=250,
                        bbox_inches="tight", facecolor=fig.get_facecolor())
            buf.seek(0)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.download_button("⬇️ Baixar PNG (alta qualidade)", buf,
                               file_name=f"ceu_{input_date.strftime('%Y%m%d')}.png",
                               mime="image/png", use_container_width=True)
        except Exception as e:
            st.error(f"Erro: {e}"); st.exception(e)

st.divider()
st.markdown("""<p style='text-align:center;font-size:11px;color:gray'>
Estrelas: <a href='https://github.com/astronexus/HYG-Database' target='_blank'>HYG Database</a> ·
Constelações: <a href='https://github.com/Stellarium/stellarium' target='_blank'>Stellarium</a> ·
Cálculos: <a href='https://www.astropy.org' target='_blank'>Astropy</a>
</p>""", unsafe_allow_html=True)