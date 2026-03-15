import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. Configuración de la página (Responsive y Título)
st.set_page_config(
    page_title="Ambitae Intelligence", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. Estilo CSS Personalizado (Colores Ambitae y corrección de métricas)
st.markdown("""
    <style>
    /* Fondo general */
    .stApp { background-color: #f8f9fa; }
    
    /* Títulos con el color corporativo */
    h1, h2, h3 { color: #1a454d !important; font-family: 'Poppins', sans-serif; }
    
    /* Estilo para que los números de las métricas no se corten */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #2e8b57 !important;
    }
    
    /* Tarjetas blancas para las métricas */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-top: 4px solid #2e8b57;
    }

    /* Ajuste para que el logo no sea gigante en móvil */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabecera Limpia (Solo un logo, el local)
col1, col2 = st.columns([1, 3])

with col1:
    # Intentamos cargar tu imagen local. Si por algo no estuviera, ponemos texto.
    try:
        st.image("ambitae-logo-completo.png", width=220)
    except:
        st.title("Ambitae")

with col2:
    st.markdown("<h1 style='margin-bottom: 0;'>Intelligence Terminal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #2e8b57; font-size: 1.2rem; font-weight: 500;'>Inteligencia ambiental al servicio de tu ciudad</p>", unsafe_allow_html=True)

st.markdown("---")

# 4. Conexión a la Base de Datos
def cargar_datos():
    try:
        conn = sqlite3.connect('contratos_menores.db')
        df = pd.read_sql_query("SELECT * FROM licitaciones", conn)
        conn.close()
        # Limpieza básica de importes
        df['importe'] = pd.to_numeric(df['importe'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

if not df.empty:
    # --- FILTROS EN BARRA LATERAL ---
    st.sidebar.header("Filtros de Búsqueda")
    buscador = st.sidebar.text_input("Buscar por concepto:", "")
    
    # Filtrado dinámico
    mask = df['titulo'].str.contains(buscador, case=False, na=False)
    df_filtrado = df[mask]

    # 5. Métricas Principales (Usando columnas para que sea responsive)
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric("Contratos Totales", f"{len(df_filtrado):,}".replace(",", "."))
    with m2:
        total_eur = df_filtrado['importe'].sum()
        # Formato abreviado si es muy grande para que no se corte
        if total_eur > 1_000_000:
            st.metric("Inversión Analizada", f"{total_eur/1_000_000:.2f} M €")
        else:
            st.metric("Inversión Analizada", f"{total_eur:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    with m3:
        st.metric("Proveedores Únicos", f"{df_filtrado['adjudicatario'].nunique():,}".replace(",", "."))

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Gráficos Interactivos
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("📍 Distribución Regional")
        resumen_comu = df_filtrado.groupby('comunidad')['importe'].sum().reset_index()
        fig_bar = px.bar(resumen_comu, x='comunidad', y='importe', 
                        color_discrete_sequence=['#1a454d'],
                        labels={'importe': 'Euros (€)', 'comunidad': 'Comunidad'})
        fig_bar.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🏆 Top 10 Adjudicatarios")
        top_10 = df_filtrado.groupby('adjudicatario')['importe'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_pie = px.pie(top_10, values='importe', names='adjudicatario', hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Greens_r)
        fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # 7. Tabla Maestra (Paginada a 100 para rendimiento)
    st.subheader("📑 Detalle de Contratos")
    st.dataframe(
        df_filtrado.head(100),
        column_config={
            "enlace": st.column_config.LinkColumn("Enlace"),
            "importe": st.column_config.NumberColumn(format="%.2f €")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.caption("Mostrando los últimos 100 resultados. Use el buscador lateral para filtrar.")

else:
    st.info("No hay datos para mostrar. Ejecuta el scraper primero.")