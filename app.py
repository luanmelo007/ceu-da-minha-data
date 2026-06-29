import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Circle
import pandas as pd
import io, requests
from datetime import datetime, date, time as dtime, timedelta

# ─── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="🌌 Céu da Minha Data", page_icon="🌌", layout="centered")
st.markdown("""<style>.block-container{max-width:760px}h1{text-align:center}</style>""",
            unsafe_allow_html=True)
st.title("🌌 Céu da Minha Data")
st.markdown("<p style='text-align:center;color:gray;margin-top:-12px'>"
            "Mapa estelar personalizado · estilo pôster</p>", unsafe_allow_html=True)

# ─── Meses em português ───────────────────────────────────────────────────────
MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

def fmt_data_pt(dt):
    return f"{dt.day} de {MESES[dt.month-1]} de {dt.year}"

def dd_to_dm(deg, is_lat):
    d   = int(abs(deg))
    m   = round((abs(deg) - d) * 60)
    suf = ("N" if deg >= 0 else "S") if is_lat else ("L" if deg >= 0 else "W")
    return f"{d}°{m:02d}'{suf}"

# ─── Nomes das constelações em português ─────────────────────────────────────
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
    "🎨 Poster Clássico (Referência)": dict(
        bg="#0c1022", sky="#0c1022",
        star="white",  star_alpha=0.92,
        line="#4a5488", line_alpha=0.55, line_w=0.7,
        name="#7a89b8", border="#3a4478",
        title="white", meta="#7a89b8",
        grid=False, compass=False,
    ),
    "🌌 Escuro Azulado": dict(
        bg="#06061f", sky="#0b0b35",
        star="white",  star_alpha=0.95,
        line="#3a3a90", line_alpha=0.5, line_w=0.7,
        name="#8888cc", border="#5050b0",
        title="white", meta="#8888cc",
        grid=True, compass=True,
    ),
    "☀️ Claro Minimalista": dict(
        bg="#f2f2f8", sky="#e8e8f4",
        star="#1a1a4e", star_alpha=0.9,
        line="#8888c0", line_alpha=0.5, line_w=0.7,
        name="#5555a0", border="#aaaacc",
        title="#1a1a4e", meta="#5555a0",
        grid=False, compass=False,
    ),
    "✨ Preto & Dourado": dict(
        bg="#080600", sky="#100d00",
        star="#ffd700", star_alpha=0.9,
        line="#604800", line_alpha=0.6, line_w=0.7,
        name="#907000", border="#806000",
        title="#ffd700", meta="#907000",
        grid=False, compass=False,
    ),
    "🌹 Rosé Romântico": dict(
        bg="#1a0a10", sky="#240e16",
        star="#ffd0e0", star_alpha=0.9,
        line="#702040", line_alpha=0.55, line_w=0.7,
        name="#c07090", border="#b04060",
        title="#ffd0e0", meta="#c07090",
        grid=False, compass=False,
    ),
}

# ─── Dados ────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="🌠 Carregando catálogo de estrelas...")
def load_stars():
    import os
    if not os.path.exists("stars.csv"):
        st.error("⚠️ Arquivo `stars.csv` não encontrado!\nExecute: `python download_stars.py`")
        st.stop()
    return pd.read_csv("stars.csv")

@st.cache_data(show_spinner="🔭 Carregando constelações...")
def load_constellations():
    base = "https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/"
    try:
        lines = requests.get(base + "constellations.lines.json", timeout=20).json()
        names = requests.get(base + "constellations.json",       timeout=20).json()
        return lines, names
    except Exception:
        return None, None

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

# ─── Constelações ─────────────────────────────────────────────────────────────
def draw_constellations(ax, frame, lines_data, names_data, show_lines, show_names, c):
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    pts_ra, pts_dec = [], []
    segments, name_items = [], []

    if show_lines and lines_data:
        for feat in lines_data.get("features", []):
            for line in feat.get("geometry", {}).get("coordinates", []):
                for i in range(len(line) - 1):
                    i0 = len(pts_ra)
                    pts_ra.extend([float(line[i][0]),   float(line[i+1][0])])
                    pts_dec.extend([float(line[i][1]),  float(line[i+1][1])])
                    segments.append((i0, i0+1))

    if show_names and names_data:
        for feat in names_data.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Point":
                abbr = feat.get("id", "")
                if abbr:
                    idx = len(pts_ra)
                    pts_ra.append(float(geom["coordinates"][0]))
                    pts_dec.append(float(geom["coordinates"][1]))
                    name_items.append((idx, abbr))

    if not pts_ra:
        return

    coords  = SkyCoord(ra=np.array(pts_ra)*u.hourangle, dec=np.array(pts_dec)*u.deg)
    altaz   = coords.transform_to(frame)
    alt_a   = altaz.alt.deg
    az_a    = altaz.az.deg
    r_a     = np.cos(np.radians(alt_a))
    x_a     =  r_a * np.sin(np.radians(az_a))
    y_a     =  r_a * np.cos(np.radians(az_a))
    vis     = alt_a > 1

    if show_lines:
        for i0, i1 in segments:
            if vis[i0] and vis[i1]:
                dx, dy = x_a[i1]-x_a[i0], y_a[i1]-y_a[i0]
                if np.sqrt(dx**2+dy**2) < 0.7:   # filtra wrap-around
                    ax.plot([x_a[i0],x_a[i1]], [y_a[i0],y_a[i1]],
                            color=c["line"], lw=c["line_w"],
                            alpha=c["line_alpha"], zorder=2, solid_capstyle="round")

    if show_names:
        for idx, abbr in name_items:
            if vis[idx] and (x_a[idx]**2 + y_a[idx]**2) < 0.86:
                ax.text(x_a[idx], y_a[idx], CONST_PT.get(abbr, abbr),
                        color=c["name"], fontsize=5.5,
                        ha="center", va="center", alpha=0.85,
                        zorder=4, style="italic", fontfamily="serif")

# ─── Geração do Mapa ─────────────────────────────────────────────────────────
def make_star_map(lat, lon, dt_utc, local_dt, title, subtitle,
                  theme_name, mag_limit, show_lines, show_names,
                  show_grid, show_compass):
    from astropy.coordinates import SkyCoord, EarthLocation, AltAz
    from astropy.time import Time
    import astropy.units as u

    stars = load_stars()
    stars = stars[stars["mag"] <= mag_limit].copy()

    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=0*u.m)
    t        = Time(dt_utc)
    frame    = AltAz(obstime=t, location=location)

    coords = SkyCoord(ra=stars["ra"].values*u.hour, dec=stars["dec"].values*u.deg)
    altaz  = coords.transform_to(frame)
    alt, az, mag = altaz.alt.deg, altaz.az.deg, stars["mag"].values

    vis  = alt > 0
    n_vis = vis.sum()
    alt, az, mag = alt[vis], az[vis], mag[vis]

    r = np.cos(np.radians(alt))
    x =  r * np.sin(np.radians(az))
    y =  r * np.cos(np.radians(az))

    c     = THEMES[theme_name]
    theta = np.linspace(0, 2*np.pi, 360)

    # ── Figura: céu em cima, textos embaixo ───────────────────────────────────
    fig = plt.figure(figsize=(7, 10), facecolor=c["bg"])

    # Área do mapa estelar (ocupa ~70% do topo)
    ax = fig.add_axes([0.05, 0.28, 0.90, 0.68])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)

    # Fundo do céu (círculo sólido)
    ax.fill(np.cos(theta), np.sin(theta), color=c["sky"], zorder=0)

    # Grade (opcional)
    if show_grid or c["grid"]:
        for alt_d in [30, 60]:
            rc = np.cos(np.radians(alt_d))
            ax.plot(rc*np.cos(theta), rc*np.sin(theta),
                    color=c["line"], lw=0.3, alpha=0.25, zorder=1, ls="--")
        for az_d in range(0, 360, 45):
            ar = np.radians(az_d)
            ax.plot([0,np.sin(ar)],[0,np.cos(ar)],
                    color=c["line"], lw=0.2, alpha=0.15, zorder=1)

    # Constelações
    if show_lines or show_names:
        ld, nd = load_constellations()
        draw_constellations(ax, frame, ld, nd, show_lines, show_names, c)

    # Estrelas — ordenadas da mais fraca à mais brilhante
    order = np.argsort(mag)[::-1]
    xo, yo, mo = x[order], y[order], mag[order]
    sizes = np.clip(5.0 - mo, 0.1, 4.5)**2 * 1.8
    ax.scatter(xo, yo, s=sizes, c=c["star"], zorder=3,
               linewidths=0, alpha=c["star_alpha"])

    # Clip circular
    clip = Circle((0,0), 1.0, transform=ax.transData)
    for a in ax.collections + ax.lines + ax.texts:
        a.set_clip_path(clip)

    # Borda do círculo — simples e fina
    ax.add_patch(Circle((0,0), 1.0, fill=False,
                         edgecolor=c["border"], lw=1.2, zorder=5, alpha=0.8))

    # Pontos cardeais (opcional)
    if show_compass or c["compass"]:
        for lbl,(cx,cy) in {"N":(0,1),"L":(1,0),"S":(0,-1),"O":(-1,0)}.items():
            ax.text(cx*1.08, cy*1.08, lbl, color=c["meta"], fontsize=9,
                    ha="center", va="center", fontweight="bold", zorder=6, alpha=0.6)

    # ── Área de texto (parte inferior da figura) ───────────────────────────────
    # Linha decorativa fina acima do título
    fig.add_artist(plt.Line2D([0.25, 0.75], [0.245, 0.245],
                               transform=fig.transFigure,
                               color=c["border"], lw=0.8, alpha=0.6))

    # Título principal — grande, serif, centralizado
    fig.text(0.5, 0.195, title, color=c["title"],
             fontsize=20, ha="center", va="center",
             fontweight="bold", fontfamily="serif")

    # Linha fina abaixo do título
    fig.add_artist(plt.Line2D([0.38, 0.62], [0.158, 0.158],
                               transform=fig.transFigure,
                               color=c["border"], lw=0.6, alpha=0.5))

    # Subtítulo (opcional)
    y_meta = 0.115
    if subtitle.strip():
        fig.text(0.5, 0.135, subtitle, color=c["meta"],
                 fontsize=9, ha="center", va="center", alpha=0.8,
                 style="italic", fontfamily="serif")
        y_meta = 0.095

    # Data em português e horário
    data_str = f"{fmt_data_pt(local_dt)}  ·  {local_dt.strftime('%H:%M')}"
    fig.text(0.5, y_meta, data_str, color=c["meta"],
             fontsize=8.5, ha="center", va="center", alpha=0.75)

    # Coordenadas em formato graus/minutos
    coord_str = f"{dd_to_dm(lat, True)}  ·  {dd_to_dm(lon, False)}"
    fig.text(0.5, y_meta - 0.03, coord_str, color=c["meta"],
             fontsize=8, ha="center", va="center", alpha=0.65)

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
        lat = st.number_input("Latitude",  value=lat_default, min_value=-90.0,  max_value=90.0,  format="%.4f")
        lon = st.number_input("Longitude", value=lon_default, min_value=-180.0, max_value=180.0, format="%.4f")

    st.divider()
    st.subheader("📅 Data e Hora")
    tz_offset = st.selectbox("Fuso horário", options=[-5,-4,-3,-2,0,1,2,3], index=2,
        format_func=lambda x: f"UTC{x:+d} {'(Brasília/Fortaleza)' if x==-3 else '(Acre)' if x==-5 else '(Manaus)' if x==-4 else '(Fernando de Noronha)' if x==-2 else '(UTC)' if x==0 else ''}")
    col1, col2 = st.columns(2)
    with col1: input_date = st.date_input("Data", value=date.today())
    with col2: input_time = st.time_input("Hora (local)", value=dtime(22, 0))
    local_dt = datetime.combine(input_date, input_time)
    dt_utc   = local_dt - timedelta(hours=tz_offset)
    st.caption(f"🕐 {fmt_data_pt(local_dt)} · {local_dt.strftime('%H:%M')}")

    st.divider()
    st.subheader("✏️ Texto")
    title    = st.text_input("Título",    value="O Céu Naquele Dia", max_chars=50)
    subtitle = st.text_input("Subtítulo (opcional)", value="", max_chars=70,
                              placeholder="Ex: o dia que o Ray nasceu")

    st.divider()
    st.subheader("🎨 Visual")
    theme     = st.selectbox("Tema", list(THEMES.keys()))
    mag_limit = st.slider("Quantidade de estrelas", 2.0, 7.0, 5.5, 0.5,
                          help="Maior = mais estrelas (inclui as mais fracas)")

    st.divider()
    st.subheader("🔭 Constelações")
    show_lines  = st.toggle("Linhas das constelações",  value=True)
    show_names  = st.toggle("Nomes das constelações",   value=True)

    st.divider()
    st.subheader("⚙️ Extras")
    show_grid    = st.toggle("Grade de altitude/azimute", value=False)
    show_compass = st.toggle("Pontos cardeais (N/S/L/O)", value=False)

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
            st.download_button("⬇️ Baixar PNG (alta qualidade)",
                               buf, file_name=f"ceu_{input_date.strftime('%Y%m%d')}.png",
                               mime="image/png", use_container_width=True)
        except ImportError:
            st.error("⚠️ Execute: `pip install astropy`")
        except Exception as e:
            st.error(f"Erro: {e}"); st.exception(e)

st.divider()
st.markdown("""<p style='text-align:center;font-size:11px;color:gray'>
Estrelas: <a href='https://github.com/astronexus/HYG-Database' target='_blank'>HYG Database</a> ·
Constelações: <a href='https://github.com/ofrohn/d3-celestial' target='_blank'>d3-celestial</a> ·
Cálculos: <a href='https://www.astropy.org' target='_blank'>Astropy</a>
</p>""", unsafe_allow_html=True)