import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(
    page_title="Ambitae Intelligence 2026",
    page_icon="🌿",
    layout="wide"
)

# 2. Estética Profesional (CSS Personalizado)
st.markdown("""
    <style>
    /* Fondo y tipografía */
    .stApp { background-color: #fcfcfc; }
    
    /* Estilo para métricas */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 6px solid #1a454d;
    }
    
    /* Títulos corporativos */
    h1, h2, h3 { color: #1a454d !important; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    
    /* Botón de enlace en la tabla */
    .stDataFrame a { color: #2e8b57 !important; text-decoration: none; font-weight: bold; }
    
    /* Ajuste de logo */
    .logo-img { float: left; margin-right: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Función de carga de datos
def cargar_datos():
    if not os.path.exists("contratos_menores.db"):
        return pd.DataFrame()
    conn = sqlite3.connect("contratos_menores.db")
    df = pd.read_sql_query("SELECT * FROM licitaciones", conn)
    conn.close()
    
    # Limpieza y formatos
    df['importe'] = pd.to_numeric(df['importe'], errors='coerce').fillna(0)
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    return df

import os
df = cargar_datos()

# --- CABECERA INTEGRADA ---
col_l, col_r = st.columns([1, 4])
with col_l:
    # Intenta cargar el logo local
    if os.path.exists("ambitae-logo-completo.png"):
        st.image("ambitae-logo-completo.png", use_container_width=True)
    else:
        st.title("🌿 Ambitae")

with col_r:
    st.markdown("<h1 style='margin-top: 10px;'>Terminal de Inteligencia Ambiental</h1>", unsafe_allow_html=True)
    st.markdown("🔍 **Análisis en tiempo real de licitaciones públicas - Año 2026**")

st.markdown("---")

if not df.empty:
    # --- PANEL IZQUIERDO: FILTROS AVANZADOS ---
    st.sidebar.header("⚙️ Panel de Control")
    
    # 1. Filtro por Título
    search = st.sidebar.text_input("Buscar por concepto:", placeholder="Ej: Mantenimiento, Residuos...")
    
    # 2. Filtros Geográficos
    comunidad_list = ["Todas"] + sorted(df['comunidad'].unique().tolist())
    com_sel = st.sidebar.selectbox("Comunidad Autónoma:", comunidad_list)
    
    provincia_list = ["Todas"] + sorted(df['provincia'].unique().tolist())
    prov_sel = st.sidebar.selectbox("Provincia:", provincia_list)
    
    # 3. FILTRO DE IMPORTE (CORREGIDO Y DINÁMICO)
    min_val = float(df['importe'].min())
    max_val = float(df['importe'].max())
    
    # Si todos los importes son iguales, ajustamos el rango para evitar error de Streamlit
    if min_val == max_val:
        min_val = 0.0
        
    rango_imp = st.sidebar.slider(
        "Rango económico (€):",
        min_value=min_val,
        max_value=max_val,
        value=(min_val, max_val),
        format="%.0f €"
    )

    # --- APLICACIÓN DE FILTROS ---
    mask = (df['importe'] >= rango_imp[0]) & (df['importe'] <= rango_imp[1])
    
    if search:
        mask &= df['titulo'].str.contains(search, case=False, na=False)
    if com_sel != "Todas":
        mask &= (df['comunidad'] == com_sel)
    if prov_sel != "Todas":
        mask &= (df['provincia'] == prov_sel)
        
    df_filtrado = df[mask]

    # --- MÉTRICAS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Licitaciones", f"{len(df_filtrado)}")
    m2.metric("Inversión Total", f"{df_filtrado['importe'].sum():,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Importe Máximo", f"{df_filtrado['importe'].max():,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    m4.metric("Adjudicatarios", f"{df_filtrado['adjudicatario'].nunique()}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📍 Inversión por Comunidad")
        fig_com = px.bar(
            df_filtrado.groupby('comunidad')['importe'].sum().reset_index(),
            x='comunidad', y='importe',
            color_discrete_sequence=['#1a454d'],
            template="plotly_white"
        )
        st.plotly_chart(fig_com, use_container_width=True)

    with g2:
        st.subheader("🏆 Principales Adjudicatarios")
        top_adj = df_filtrado.groupby('adjudicatario')['importe'].sum().nlargest(10).reset_index()
        fig_pie = px.pie(
            top_adj, values='importe', names='adjudicatario',
            hole=0.4, color_discrete_sequence=px.colors.sequential.Greens_r
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABLA MAESTRA ---
    st.subheader("📑 Detalle de Contratos (2026)")
    st.dataframe(
        df_filtrado,
        column_config={
            "enlace": st.column_config.LinkColumn("🔗 Perfil Contratante", display_text="Ver Licitación"),
            "importe": st.column_config.NumberColumn("Importe (€)", format="%.2f €"),
            "fecha": st.column_config.DateColumn("Fecha"),
            "titulo": "Concepto",
            "adjudicatario": "Empresa"
        },
        use_container_width=True,
        hide_index=True
    )

else:
    st.error("❌ No se han detectado datos en 'contratos_menores.db'. Por favor, ejecuta primero el scraper.")

# Pie de página
st.markdown("---")
st.caption("Ambitae Intelligence v2.0 | Datos procesados desde Plataforma de Contratación del Estado")