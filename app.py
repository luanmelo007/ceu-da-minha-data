import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
            "Mapa estelar gratuito e personalizado para qualquer momento e lugar</p>",
            unsafe_allow_html=True)

# ─── Nomes das constelações em português ──────────────────────────────────────

CONST_PT = {
    "And":"Andrômeda",    "Ant":"Máq. Pneumática","Aps":"Ave do Paraíso",
    "Aqr":"Aquário",      "Aql":"Águia",          "Ara":"Altar",
    "Ari":"Áries",        "Aur":"Cocheiro",        "Boo":"Boieiro",
    "Cae":"Cinzel",       "Cam":"Girafa",          "Cnc":"Câncer",
    "CVn":"Cães de Caça", "CMa":"Cão Maior",       "CMi":"Cão Menor",
    "Cap":"Capricórnio",  "Car":"Quilha",          "Cas":"Cassiopeia",
    "Cen":"Centauro",     "Cep":"Cefeu",           "Cet":"Baleia",
    "Cha":"Camaleão",     "Cir":"Compasso",        "Col":"Pomba",
    "Com":"Cab. Berenice","CrA":"Coroa Austral",   "CrB":"Coroa Boreal",
    "Crv":"Corvo",        "Crt":"Taça",            "Cru":"Cruzeiro do Sul",
    "Cyg":"Cisne",        "Del":"Golfinho",        "Dor":"Dourado",
    "Dra":"Dragão",       "Equ":"Potro",           "Eri":"Erídano",
    "For":"Fornalha",     "Gem":"Gêmeos",          "Gru":"Grou",
    "Her":"Hércules",     "Hor":"Relógio",         "Hya":"Hidra",
    "Hyi":"Hidra Macho",  "Ind":"Índio",           "Lac":"Lagartixa",
    "Leo":"Leão",         "LMi":"Leão Menor",      "Lep":"Lebre",
    "Lib":"Balança",      "Lup":"Lobo",            "Lyn":"Lince",
    "Lyr":"Lira",         "Men":"Mesa",            "Mic":"Microscópio",
    "Mon":"Unicórnio",    "Mus":"Mosca",           "Nor":"Esquadro",
    "Oct":"Oitante",      "Oph":"Ofiúco",          "Ori":"Órion",
    "Pav":"Pavão",        "Peg":"Pégaso",          "Per":"Perseu",
    "Phe":"Fênix",        "Pic":"Pintor",          "PsA":"Peixe Austral",
    "Psc":"Peixes",       "Pup":"Popa",            "Pyx":"Bússola",
    "Ret":"Retículo",     "Sge":"Flecha",          "Sgr":"Sagitário",
    "Sco":"Escorpião",    "Scl":"Escultor",        "Sct":"Escudo",
    "Ser":"Serpente",     "Sex":"Sextante",        "Tau":"Touro",
    "Tel":"Telescópio",   "TrA":"Triâng. Austral", "Tri":"Triângulo",
    "Tuc":"Tucano",       "UMa":"Ursa Maior",      "UMi":"Ursa Menor",
    "Vel":"Vela",         "Vir":"Virgem",          "Vol":"Peixe Voador",
    "Vul":"Raposa",
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
    """
    Carrega linhas e centros das constelações do d3-celestial (BSD license).
    Coordenadas: RA em horas (0-24), Dec em graus.
    """
    base = "https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/"
    try:
        lines = requests.get(base + "constellations.lines.json", timeout=20).json()
        names = requests.get(base + "constellations.json",       timeout=20).json()
        return lines, names
    except Exception as e:
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

# ─── Cor das estrelas ─────────────────────────────────────────────────────────

def bv_to_color(bv):
    if np.isnan(bv): return "#ffffff"
    if bv < -0.30: return "#9bb8ff"
    if bv < -0.10: return "#aac4ff"
    if bv <  0.10: return "#cad8ff"
    if bv <  0.30: return "#f0f4ff"
    if bv <  0.58: return "#fff7e8"
    if bv <  0.81: return "#ffd49e"
    if bv <  1.40: return "#ffb86c"
    return "#ff8c5a"

# ─── Temas ────────────────────────────────────────────────────────────────────

THEMES = {
    "🌌 Escuro Clássico": dict(
        bg="#06061f", sky_inner="#0d1240", sky_outer="#06061f",
        grid="#1a1a50", border="#5050b0", text="white", compass="#8888cc",
        const_line="#3a3a90", const_name="#9090cc", use_star_colors=True),
    "🌊 Azul Profundo": dict(
        bg="#010d1f", sky_inner="#031a45", sky_outer="#010d1f",
        grid="#062a6a", border="#1a5ccc", text="#b0d0f8", compass="#5590e0",
        const_line="#1a4090", const_name="#6090d0", use_star_colors=True),
    "☀️ Claro Minimalista": dict(
        bg="#f0f0f8", sky_inner="#e4e4f4", sky_outer="#c8c8e8",
        grid="#b8b8d8", border="#5050a0", text="#1a1a5e", compass="#7070b0",
        const_line="#8888c0", const_name="#5050a0", use_star_colors=False),
    "✨ Preto & Dourado": dict(
        bg="#080600", sky_inner="#130f00", sky_outer="#080600",
        grid="#201800", border="#806000", text="#ffd700", compass="#c09000",
        const_line="#503800", const_name="#907000", use_star_colors=False),
    "🌹 Rosé Romântico": dict(
        bg="#1a0a10", sky_inner="#2e0f1c", sky_outer="#1a0a10",
        grid="#401525", border="#b04060", text="#ffd0e0", compass="#e08888",
        const_line="#702040", const_name="#c07080", use_star_colors=False),
    "🟢 Verde Hacker": dict(
        bg="#000a00", sky_inner="#001800", sky_outer="#000a00",
        grid="#003300", border="#007700", text="#00ff88", compass="#00cc66",
        const_line="#004400", const_name="#00aa44", use_star_colors=False),
}

# ─── Desenho das constelações ─────────────────────────────────────────────────

def draw_constellations(ax, frame, lines_data, names_data,
                        show_lines, show_names, c):
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    # ── coleta todos os pontos únicos para transformação em lote ─────────────
    points_ra, points_dec = [], []
    segments   = []   # (idx_a, idx_b)
    name_items = []   # (idx, abbr)

    if show_lines and lines_data:
        for feat in lines_data.get("features", []):
            feat_id = feat.get("id", "")
            for line in feat.get("geometry", {}).get("coordinates", []):
                for i in range(len(line) - 1):
                    # RA em horas, Dec em graus (d3-celestial)
                    ra0, dec0 = float(line[i][0]),   float(line[i][1])
                    ra1, dec1 = float(line[i+1][0]), float(line[i+1][1])
                    i0 = len(points_ra)
                    points_ra.extend([ra0, ra1])
                    points_dec.extend([dec0, dec1])
                    segments.append((i0, i0+1))

    if show_names and names_data:
        for feat in names_data.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Point":
                ra, dec = geom["coordinates"]
                abbr = feat.get("id", "")
                if abbr:
                    idx = len(points_ra)
                    points_ra.append(float(ra))
                    points_dec.append(float(dec))
                    name_items.append((idx, abbr))

    if not points_ra:
        return

    # ── transformação em lote ─────────────────────────────────────────────────
    coords  = SkyCoord(ra=np.array(points_ra)  * u.hourangle,
                       dec=np.array(points_dec) * u.deg)
    altaz   = coords.transform_to(frame)
    alt_arr = altaz.alt.deg
    az_arr  = altaz.az.deg

    r_arr = np.cos(np.radians(alt_arr))
    x_arr =  r_arr * np.sin(np.radians(az_arr))
    y_arr =  r_arr * np.cos(np.radians(az_arr))
    vis   = alt_arr > 1   # margem de 1° acima do horizonte

    # ── linhas ────────────────────────────────────────────────────────────────
    if show_lines:
        for i0, i1 in segments:
            if not (vis[i0] and vis[i1]):
                continue
            dx = x_arr[i1] - x_arr[i0]
            dy = y_arr[i1] - y_arr[i0]
            # FILTRO PRINCIPAL: descarta segmentos impossíveis
            # (causados por estrelas que cruzam o limite RA=0h/24h)
            dist_proj = np.sqrt(dx**2 + dy**2)
            if dist_proj > 0.7:
                continue
            ax.plot([x_arr[i0], x_arr[i1]],
                    [y_arr[i0], y_arr[i1]],
                    color=c["const_line"], lw=0.8,
                    alpha=0.55, zorder=2)

    # ── nomes em português ────────────────────────────────────────────────────
    if show_names:
        for idx, abbr in name_items:
            if not vis[idx]:
                continue
            if x_arr[idx]**2 + y_arr[idx]**2 > 0.86:
                continue
            nome = CONST_PT.get(abbr, abbr)
            ax.text(x_arr[idx], y_arr[idx], nome,
                    color=c["const_name"], fontsize=5.5,
                    ha="center", va="center",
                    alpha=0.85, zorder=4,
                    style="italic", fontfamily="serif")

# ─── Geração do Mapa ─────────────────────────────────────────────────────────

def make_star_map(lat, lon, dt_utc, title, subtitle, theme_name,
                  mag_limit, show_const_lines, show_const_names):
    from astropy.coordinates import SkyCoord, EarthLocation, AltAz
    from astropy.time import Time
    import astropy.units as u

    stars  = load_stars()
    stars  = stars[stars["mag"] <= mag_limit].copy()

    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=0 * u.m)
    t        = Time(dt_utc)
    frame    = AltAz(obstime=t, location=location)

    coords = SkyCoord(ra=stars["ra"].values * u.hour,
                      dec=stars["dec"].values * u.deg)
    altaz  = coords.transform_to(frame)
    alt    = altaz.alt.deg
    az     = altaz.az.deg
    mag    = stars["mag"].values
    ci     = stars["ci"].values if "ci" in stars.columns else np.full(len(stars), np.nan)

    vis = alt > 0
    n_vis = vis.sum()
    alt, az, mag, ci = alt[vis], az[vis], mag[vis], ci[vis]

    r = np.cos(np.radians(alt))
    x =  r * np.sin(np.radians(az))
    y =  r * np.cos(np.radians(az))

    c = THEMES[theme_name]

    # ── Figura ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(8, 10.5), facecolor=c["bg"])
    ax  = fig.add_axes([0.08, 0.11, 0.84, 0.72])
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-1.18, 1.18); ax.set_ylim(-1.18, 1.18)

    theta = np.linspace(0, 2 * np.pi, 360)

    # Gradiente de fundo
    n_rings = 60
    for i in range(n_rings, 0, -1):
        blend = i / n_rings
        inner = mcolors.to_rgb(c["sky_inner"])
        outer = mcolors.to_rgb(c["sky_outer"])
        col   = tuple(inner[j]*(1-blend) + outer[j]*blend for j in range(3))
        ax.fill(i/n_rings * np.cos(theta), i/n_rings * np.sin(theta),
                color=col, zorder=0)

    # Grade
    for alt_deg in [30, 60]:
        rc = np.cos(np.radians(alt_deg))
        ax.plot(rc*np.cos(theta), rc*np.sin(theta),
                color=c["grid"], lw=0.5, alpha=0.35, zorder=1, ls="--")
    for az_d in range(0, 360, 30):
        ar = np.radians(az_d)
        ax.plot([0, np.sin(ar)], [0, np.cos(ar)],
                color=c["grid"], lw=0.3, alpha=0.2, zorder=1)

    # ── Constelações (antes das estrelas) ─────────────────────────────────────
    if show_const_lines or show_const_names:
        lines_data, names_data = load_constellations()
        if lines_data or names_data:
            draw_constellations(ax, frame, lines_data, names_data,
                                show_const_lines, show_const_names, c)
        else:
            st.warning("⚠️ Não foi possível carregar dados de constelações.")

    # ── Estrelas ──────────────────────────────────────────────────────────────
    order = np.argsort(mag)[::-1]
    x, y, mag, ci = x[order], y[order], mag[order], ci[order]

    if c["use_star_colors"]:
        colors = [bv_to_color(b) for b in ci]
    else:
        colors = [c["compass"]] * len(x)

    sizes_core = np.clip(5.5 - mag, 0.15, 5.0) ** 2 * 2.8
    sizes_glow = sizes_core * 6

    for i in range(len(x)):
        ax.scatter(x[i], y[i], s=sizes_glow[i], c=[colors[i]],
                   alpha=0.07, zorder=3, linewidths=0)
    ax.scatter(x, y, s=sizes_core, c=colors, zorder=4, linewidths=0, alpha=0.97)

    bright = mag < 1.5
    if bright.any():
        ax.scatter(x[bright], y[bright], s=sizes_glow[bright]*3,
                   c=[colors[i] for i in np.where(bright)[0]],
                   alpha=0.05, zorder=3, linewidths=0)

    # Clip circular
    clip = Circle((0, 0), 1.0, transform=ax.transData)
    for artist in ax.collections + ax.lines + ax.texts:
        artist.set_clip_path(clip)

    # Bordas
    ax.add_patch(Circle((0,0), 1.02, fill=False,
                         edgecolor=c["border"], lw=0.5, alpha=0.4, zorder=6))
    ax.add_patch(Circle((0,0), 1.00, fill=False,
                         edgecolor=c["border"], lw=2.0, zorder=6))

    # Pontos cardeais
    for lbl,(cx,cy) in {"N":(0,1),"L":(1,0),"S":(0,-1),"O":(-1,0)}.items():
        ax.text(cx*1.1, cy*1.1, lbl, color=c["compass"], fontsize=11,
                ha="center", va="center", fontweight="bold", zorder=7)

    # ── Textos da figura ──────────────────────────────────────────────────────
    fig.text(0.5, 0.905, title, color=c["text"], fontsize=15,
             ha="center", fontweight="bold", fontfamily="serif")
    if subtitle.strip():
        fig.text(0.5, 0.873, subtitle, color=c["text"], fontsize=9,
                 ha="center", alpha=0.75)
    line_y = 0.862 if subtitle.strip() else 0.885
    fig.add_artist(plt.Line2D([0.2,0.8],[line_y-0.008]*2,
                               transform=fig.transFigure,
                               color=c["border"], lw=0.8, alpha=0.5))
    fig.text(0.5, 0.065,
             f"Lat {lat:+.4f}°   Lon {lon:+.4f}°   ·   "
             f"{dt_utc.strftime('%d/%m/%Y  %H:%M')} UTC",
             color=c["text"], fontsize=7, ha="center", alpha=0.45)
    fig.text(0.5, 0.038,
             f"{n_vis:,} estrelas visíveis  ·  magnitude ≤ {mag_limit}  ·  HYG Database / Astropy",
             color=c["text"], fontsize=6.5, ha="center", alpha=0.35)
    return fig

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configurações")

    st.subheader("📍 Localização")
    loc_mode = st.radio("Modo", ["🔍 Buscar cidade", "🗺️ Lat/Lon manual"],
                        label_visibility="collapsed")
    lat_default, lon_default = -3.6880, -40.3497

    if loc_mode == "🔍 Buscar cidade":
        city_input = st.text_input("Cidade", value="Sobral, Ceará, Brasil")
        if st.button("🔍 Buscar coordenadas"):
            with st.spinner("Buscando..."):
                la, lo, display = geocode_city(city_input)
            if la:
                st.session_state["lat"] = la
                st.session_state["lon"] = lo
                st.success(f"✅ {display[:70]}")
            else:
                st.error("❌ Cidade não encontrada.")
        lat = st.session_state.get("lat", lat_default)
        lon = st.session_state.get("lon", lon_default)
        st.caption(f"📌 Lat {lat:.4f}° · Lon {lon:.4f}°")
    else:
        lat = st.number_input("Latitude",  value=lat_default, min_value=-90.0,  max_value=90.0,  format="%.4f")
        lon = st.number_input("Longitude", value=lon_default, min_value=-180.0, max_value=180.0, format="%.4f")

    st.divider()
    st.subheader("📅 Data e Hora")
    tz_offset = st.selectbox("Fuso horário", options=[-5,-4,-3,-2,0,1,2,3], index=2,
        format_func=lambda x: f"UTC{x:+d}  {'(Brasília/Fortaleza)' if x==-3 else '(Acre)' if x==-5 else '(Manaus)' if x==-4 else '(Fernando de Noronha)' if x==-2 else '(UTC)' if x==0 else ''}")
    col1, col2 = st.columns(2)
    with col1: input_date = st.date_input("Data", value=date.today())
    with col2: input_time = st.time_input("Hora (local)", value=dtime(22, 0))
    local_dt = datetime.combine(input_date, input_time)
    dt_utc   = local_dt - timedelta(hours=tz_offset)
    st.caption(f"🕐 {local_dt.strftime('%d/%m/%Y %H:%M')} → {dt_utc.strftime('%H:%M')} UTC")

    st.divider()
    st.subheader("✏️ Personalização")
    title     = st.text_input("Título",    value="O Céu Naquele Dia",               max_chars=60)
    subtitle  = st.text_input("Subtítulo", value="Um momento especial sob as estrelas", max_chars=80)
    theme     = st.selectbox("Tema de cores", list(THEMES.keys()))
    mag_limit = st.slider("Quantidade de estrelas", 2.0, 7.0, 5.5, 0.5,
                          help="Valor maior = mais estrelas")

    st.divider()
    st.subheader("🔭 Constelações")
    show_const_lines = st.toggle("Mostrar linhas das constelações", value=False)
    show_const_names = st.toggle("Mostrar nomes das constelações",  value=False)

# ─── Botão e resultado ────────────────────────────────────────────────────────

st.divider()

if st.button("🌌 Gerar Mapa Estelar", type="primary", use_container_width=True):
    with st.spinner("✨ Calculando posições das estrelas..."):
        try:
            fig = make_star_map(lat, lon, dt_utc, title, subtitle, theme,
                                mag_limit, show_const_lines, show_const_names)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200,
                        bbox_inches="tight", facecolor=fig.get_facecolor())
            buf.seek(0)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.download_button("⬇️ Baixar PNG em alta qualidade", buf,
                               file_name=f"ceu_{input_date.strftime('%Y%m%d')}.png",
                               mime="image/png", use_container_width=True)
            st.success("Mapa gerado! Clique em Baixar para salvar.")
        except ImportError:
            st.error("⚠️ Execute: `pip install astropy`")
        except Exception as e:
            st.error(f"Erro: {e}")
            st.exception(e)

st.divider()
st.markdown("""<p style='text-align:center;font-size:11px;color:gray'>
Estrelas: <a href='https://github.com/astronexus/HYG-Database' target='_blank'>HYG Database</a> ·
Constelações: <a href='https://github.com/ofrohn/d3-celestial' target='_blank'>d3-celestial</a> ·
Cálculos: <a href='https://www.astropy.org' target='_blank'>Astropy</a>
</p>""", unsafe_allow_html=True)