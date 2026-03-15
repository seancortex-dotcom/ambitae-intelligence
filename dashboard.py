import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# Configuración de página con título dinámico
st.set_page_config(page_title="Ambitae Intelligence", layout="wide")

# CSS Ajustado para evitar solapamientos y mejorar legibilidad en web
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; font-weight: bold; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    .main-title { color: #1a454d; font-size: 2rem; font-weight: bold; margin-bottom: 0; }
    /* Evita que los KPIs se peguen en pantallas pequeñas */
    div[data-testid="stHorizontalBlock"] > div { min-width: 150px !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if not os.path.exists('contratos_menores.db'):
        return pd.DataFrame()
    conn = sqlite3.connect('contratos_menores.db')
    df = pd.read_sql_query("SELECT * FROM licitaciones", conn)
    conn.close()
    df['importe'] = pd.to_numeric(df['importe'], errors='coerce').fillna(0)
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    return df

df = cargar_datos()

# Cabecera optimizada
col_logo, col_tit = st.columns([1, 3])
with col_logo:
    if os.path.exists("ambitae-logo-completo.png"):
        st.image("ambitae-logo-completo.png", width=180)
with col_tit:
    st.markdown('<p class="main-title">Intelligence Terminal</p>', unsafe_allow_html=True)
    st.caption("Inteligencia ambiental al servicio de tu ciudad | Datos 2026")

if not df.empty:
    # Sidebar - Filtros
    st.sidebar.header("Filtros de Búsqueda")
    
    # Búsqueda por concepto mejorada
    search = st.sidebar.text_input("Buscar por concepto:", key="search_input")
    
    comunidad_sel = st.sidebar.selectbox("Comunidad:", ["Todas"] + sorted(df['comunidad'].unique().tolist()))
    
    # Rango de importe dinámico
    min_imp, max_imp = float(df['importe'].min()), float(df['importe'].max())
    rango = st.sidebar.slider("Rango Importe (€):", min_imp, max_imp, (min_imp, max_imp))

    # Lógica de filtrado estricta
    df_f = df.copy()
    if search:
        # Filtramos por título o adjudicatario para que la búsqueda sea potente
        df_f = df_f[df_f['titulo'].str.contains(search, case=False, na=False) | 
                    df_f['adjudicatario'].str.contains(search, case=False, na=False)]
    
    if comunidad_sel != "Todas":
        df_f = df_f[df_f['comunidad'] == comunidad_sel]
        
    df_f = df_f[(df_f['importe'] >= rango[0]) & (df_f['importe'] <= rango[1])]

    # Métricas en columnas con más aire (usamos columns para evitar solape)
    st.write("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Contratos Totales", f"{len(df_f):,}".replace(",", "."))
    m2.metric("Inversión Analizada", f"{df_f['importe'].sum()/1e6:,.2f} M €".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Proveedores Únicos", f"{df_f['adjudicatario'].nunique():,}".replace(",", "."))

    # Gráficos
    st.write("### Análisis Visual")
    c1, c2 = st.columns([2, 1])
    with c1:
        fig_bar = px.bar(df_f.groupby('comunidad')['importe'].sum().reset_index(), 
                         x='comunidad', y='importe', title="Distribución Regional",
                         color_discrete_sequence=['#1a454d'])
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        top_10 = df_f.groupby('adjudicatario')['importe'].sum().nlargest(10).reset_index()
        fig_pie = px.pie(top_10, values='importe', names='adjudicatario', title="Top 10 Adjudicatarios",
                         hole=0.3, color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabla Detallada
    st.write("### Listado de Licitaciones")
    st.dataframe(
        df_f[['fecha', 'titulo', 'importe', 'adjudicatario', 'enlace']],
        column_config={
            "enlace": st.column_config.LinkColumn("Enlace", display_text="Ver Perfil"),
            "importe": st.column_config.NumberColumn("Euros", format="%.2f €"),
            "fecha": st.column_config.DateColumn("Fecha")
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.error("No se han cargado los datos correctamente.")