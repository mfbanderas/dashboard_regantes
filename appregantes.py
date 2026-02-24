# streamlit run appregantes.py
# streamlit run appregantes.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Monitor Avance | Comunidades Regantes",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. PALETA DE COLORES ACUÁTICOS ---
C_AQUA      = '#00B4D8' # Celeste vibrante (Color Principal)
C_TEAL      = '#0077B6' # Azul océano profundo (Contraste)
C_TURQUOISE = '#48CAE4' # Turquesa claro
C_GREEN     = '#20B2AA' # Verde agua / Sea green
C_LIGHT     = '#90E0EF' # Celeste muy claro
C_DARK_TEXT = '#1A365D' # Azul marino oscuro para textos legibles

PALETTE_AGUA = [C_AQUA, C_TEAL, C_GREEN, C_TURQUOISE, C_LIGHT]

# --- 3. ESTILOS CSS PERSONALIZADOS (AESTHETIC & BIG NUMBERS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F4F9F9 !important; color: {C_DARK_TEXT} !important; }}
    h1, h2, h3 {{ color: {C_DARK_TEXT} !important; border-left: 5px solid {C_AQUA} !important; padding-left: 15px !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
    div[data-testid="stMetric"] {{ background-color: #FFFFFF !important; border: 1px solid #E0F2F1 !important; padding: 20px !important; border-radius: 10px; box-shadow: 0 4px 10px rgba(0, 119, 182, 0.05); text-align: center; min-height: 160px; display: flex; flex-direction: column; justify-content: center; }}
    [data-testid="stMetricLabel"] {{ color: #5F7A8C !important; font-size: 1.1rem !important; font-weight: 600 !important; text-transform: uppercase; }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{ color: {C_AQUA} !important; font-size: 45px !important; font-weight: 800 !important; line-height: 1.2 !important; }}
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stVerticalBlock"] {{ background-color: #FFFFFF !important; border: 1px solid #E0F2F1 !important; border-radius: 10px; box-shadow: 0 4px 10px rgba(0, 119, 182, 0.05); padding: 10px; height: 160px; display: flex; align-items: center; justify-content: center; }}
    [data-testid="stSidebar"] {{ background-color: #FFFFFF !important; border-right: 1px solid #E0F2F1; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def load_data():
    # Nombre del nuevo archivo
    file_name = 'results-survey959375.csv' 
    
    try:
        # El nuevo archivo usa punto y coma como separador
        df = pd.read_csv(file_name, sep=';', encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_name, sep=',', encoding='utf-8')
        except:
            return None

    # ESTRATEGIA DE RENOMBRADO INTELIGENTE
    rename_map = {}
    for col in df.columns:
        if 'Nombre de la' in col: rename_map[col] = 'Nombre de la Comunidad de Regantes (CC.RR.)'
        elif 'Provincia' in col: rename_map[col] = 'Provincia'
        elif 'Demarcación' in col: rename_map[col] = 'Demarcación Hidrográfica'
        elif 'comuneros' in col: rename_map[col] = 'Número de comuneros'
        elif 'Superficie' in col: rename_map[col] = 'Superficie total del área de riego en Has.'
        elif 'Fecha' in col: rename_map[col] = 'Fecha'

    df = df.rename(columns=rename_map)
    df.columns = df.columns.str.strip()
    
    # Relleno de datos faltantes para evitar errores
    cols_categoricas = ['Provincia', 'Demarcación Hidrográfica', 'Nombre de la Comunidad de Regantes (CC.RR.)']
    for col in cols_categoricas:
        if col in df.columns:
            df[col] = df[col].fillna("Sin especificar")

    cols_numericas = ['Número de comuneros', 'Superficie total del área de riego en Has.']
    for col in cols_numericas:
        if col in df.columns:
            # Quitamos posibles comas de miles antes de convertir a número
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Procesamiento de Fechas (formato detectado: DD-MM-YYYY)
    if 'Fecha' in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], format='%d-%m-%Y', errors='coerce')
        # Fallback de seguridad
        df['Fecha_dt'] = df['Fecha_dt'].fillna(pd.Timestamp.today())
        
    return df

# --- 5. LÓGICA PRINCIPAL ---
try:
    df = load_data()
    
    if df is None:
        st.error("⚠️ No se pudo leer el archivo 'results-survey959375.csv'. Verifica que el nombre sea correcto.")
    else:
        # Inicialización segura de variables de filtro
        filtro_dem = []
        inicio, fin = None, None

        # --- SIDEBAR (FILTROS) ---
        with st.sidebar:
            st.header("🎛️ Filtros")
            
            # Filtro Demarcación Hidrográfica
            if "Demarcación Hidrográfica" in df.columns:
                demarcaciones = sorted(df["Demarcación Hidrográfica"].unique())
                sel_dem = st.multiselect("Demarcación Hidrográfica:", ["Todas"] + list(demarcaciones), default=["Todas"])
                filtro_dem = demarcaciones if "Todas" in sel_dem else sel_dem
            
            # Filtro Fecha
            if 'Fecha_dt' in df.columns:
                min_d, max_d = df['Fecha_dt'].min().date(), df['Fecha_dt'].max().date()
                fechas = st.date_input("Fechas:", (min_d, max_d))
                inicio, fin = fechas if isinstance(fechas, tuple) and len(fechas)==2 else (min_d, max_d)

        # Aplicar Filtros (con validación para que no salte KeyError)
        if "Demarcación Hidrográfica" in df.columns and 'Fecha_dt' in df.columns:
            mask = (df["Demarcación Hidrográfica"].isin(filtro_dem)) & \
                   (df['Fecha_dt'].dt.date >= inicio) & (df['Fecha_dt'].dt.date <= fin)
            df_filtered = df[mask]
        else:
            df_filtered = df 

        # --- CABECERA ---
        col_logo, col_titulo = st.columns([1, 5])
        
        with col_logo:
            # Si tu imagen se llama diferente a "logo.png", cambia el nombre justo aquí abajo
            st.image("logo.png", use_container_width=True)
            
        with col_titulo:
            st.markdown(f"<h1>Monitor de Avance | <span style='color:{C_AQUA}'>Comunidades de Regantes</span></h1>", unsafe_allow_html=True)
            st.markdown("Visión general del registro y caracterización de las Comunidades de Regantes.")
            
        st.markdown("<br>", unsafe_allow_html=True)

        # --- SECCIÓN KPIs ---
        META = 104 # <--- ¡META ACTUALIZADA A 104 ENCUESTAS!
        total_real = len(df) 
        pct_avance = min((total_real / META) * 100, 100)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Respuestas Registradas", len(df_filtered)) 
        c2.metric("Meta Objetivo", META)
        c3.metric("Faltantes", max(0, META - total_real))
        
        with c4:
            # GAUGE (MEDIDOR)
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number", value = pct_avance,
                title = {'text': "AVANCE GLOBAL", 'font': {'size': 12, 'color': C_DARK_TEXT}},
                number = {'suffix': "%", 'font': {'size': 30, 'color': C_AQUA, 'weight': 'bold'}}, 
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 0, 'tickcolor': "white"},
                    'bar': {'color': C_AQUA},
                    'bgcolor': "#E0F2F1",
                    'borderwidth': 0,
                    'bordercolor': "white"
                }
            ))
            fig_g.update_layout(
                height=140, margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)', font={'family': "Arial"}
            )
            st.plotly_chart(fig_g, use_container_width=True)

        st.markdown("---")

        # --- FUNCIÓN DE ESTILO DE GRÁFICOS ---
        def aplicar_estilo(fig, mt=30):
            fig.update_layout(
                paper_bgcolor='white', plot_bgcolor='white',
                font={'color': C_DARK_TEXT, 'size': 14}, 
                margin=dict(l=20, r=50, t=mt, b=20), 
                showlegend=False
            )
            fig.update_xaxes(showline=True, linewidth=1, linecolor='#B2EBF2', gridcolor='#E0F2F1', zeroline=False)
            fig.update_yaxes(showline=True, linewidth=1, linecolor='#B2EBF2', gridcolor='#E0F2F1', zeroline=False)
            return fig

        # --- GRÁFICOS TEMPORALES Y GEOGRÁFICOS ---
        st.markdown("### Dinámica de Registro")
        g1, g2 = st.columns((2, 1))
        
        with g1:
            st.markdown(f"**<span style='color:{C_TEAL}'>📅 Evolución Diaria de Registros</span>**", unsafe_allow_html=True)
            if 'Fecha_dt' in df_filtered.columns and not df_filtered.empty:
                # 1. Convertimos la fecha a formato string (DD-MM-YYYY) para evitar horas
                df_filtered['Fecha'] = df_filtered['Fecha_dt'].dt.strftime('%d-%m-%Y')
                
                # 2. Agrupamos por la nueva columna 'Fecha'
                diario = df_filtered.groupby('Fecha').size().reset_index(name='N')
                
                # 3. Graficamos indicando x='Fecha'
                fig1 = px.line(diario, x='Fecha', y='N', markers=True, text='N')
                fig1.update_traces(
                    line_color=C_TEAL, marker_color=C_AQUA, 
                    line_width=3, marker_size=10,
                    textposition="top center", textfont_size=16           
                )
                
                fig1 = aplicar_estilo(fig1)
                
                # 4. Forzamos a Plotly a tratar el eje como categórico (solo los días exactos que existen)
                fig1.update_xaxes(type='category', title_text='Fecha')
                
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Sin datos de fecha suficientes para graficar.")
            
        with g2:
            st.markdown(f"**<span style='color:{C_TEAL}'>📍 Registros por Provincia</span>**", unsafe_allow_html=True)
            if 'Provincia' in df_filtered.columns and not df_filtered.empty:
                prov = df_filtered['Provincia'].value_counts().head(5).reset_index()
                prov.columns = ['Provincia', 'N']
                fig2 = px.bar(prov, x='Provincia', y='N', text='N', color_discrete_sequence=[C_TURQUOISE])
                fig2.update_traces(textposition='outside')
                fig2 = aplicar_estilo(fig2, mt=25) 
                st.plotly_chart(fig2, use_container_width=True)

        # --- CARACTERÍSTICAS DE LAS COMUNIDADES ---
        st.markdown("### Perfil de las Comunidades de Regantes")
        g3, g4 = st.columns(2)
        
        with g3:
            st.markdown(f"**<span style='color:{C_TEAL}'>Demarcación Hidrográfica</span>**", unsafe_allow_html=True)
            if 'Demarcación Hidrográfica' in df_filtered.columns and not df_filtered.empty:
                dem = df_filtered['Demarcación Hidrográfica'].value_counts().reset_index()
                dem.columns = ['Demarcación', 'N']
                fig3 = px.pie(dem, values='N', names='Demarcación', hole=0.5, color_discrete_sequence=PALETTE_AGUA)
                fig3.update_layout(
                    paper_bgcolor='white', font={'color': C_DARK_TEXT, 'size': 16},
                    margin=dict(l=20, r=50, t=30, b=20),
                    legend=dict(orientation="h", y=-0.2, font=dict(size=12))
                )
                st.plotly_chart(fig3, use_container_width=True)
                
        with g4:
            st.markdown(f"**<span style='color:{C_TEAL}'>Top 5 Superficie total Área de Riego (Has.) por Comunidad Regante</span>**", unsafe_allow_html=True)
            if 'Superficie total del área de riego en Has.' in df_filtered.columns and not df_filtered.empty:
                sup = df_filtered.nlargest(5, 'Superficie total del área de riego en Has.')[['Nombre de la Comunidad de Regantes (CC.RR.)', 'Superficie total del área de riego en Has.']]
                sup.columns = ['CC.RR.', 'Hectáreas']
                if sup['Hectáreas'].sum() > 0:
                    fig4 = px.bar(sup, y='CC.RR.', x='Hectáreas', orientation='h', text='Hectáreas', color_discrete_sequence=[C_AQUA])
                    fig4.update_traces(textposition='inside', textfont_color='white')
                    fig4 = aplicar_estilo(fig4)
                    fig4.update_yaxes(autorange="reversed") 
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Aún no se han introducido datos de superficie en las encuestas.")

        # --- DISTRIBUCIÓN DE COMUNEROS ---
        st.markdown(f"### Comunidades con Mayor Número de Comuneros (Top 15)")
        if 'Número de comuneros' in df_filtered.columns and not df_filtered.empty:
            comuneros = df_filtered.nlargest(15, 'Número de comuneros')[['Nombre de la Comunidad de Regantes (CC.RR.)', 'Número de comuneros']]
            comuneros.columns = ['CC.RR.', 'Comuneros']
            if comuneros['Comuneros'].sum() > 0:
                fig5 = px.bar(comuneros, x='CC.RR.', y='Comuneros', text='Comuneros', color_discrete_sequence=[C_GREEN])
                
                # Evitar que el texto sobre la barra sea recortado por el borde del gráfico
                fig5.update_traces(textposition='outside', cliponaxis=False)
                fig5 = aplicar_estilo(fig5)
                
                # Agrandar altura, ajustar márgenes para que entren los números y los textos largos
                fig5.update_layout(
                    height=600,                           # <-- ALTURA DEL GRÁFICO (puedes subirlo a 700 si necesitas más)
                    margin=dict(t=40, b=150, l=20, r=20)  # <-- t=40 da espacio al número superior, b=150 al texto inferior
                )
                
                # Rotar los nombres de las CC.RR. en diagonal para que no se superpongan
                fig5.update_xaxes(tickangle=-45)
                
                st.plotly_chart(fig5, use_container_width=True)
            else:
                 st.info("Aún no se han introducido datos de comuneros en las encuestas.")

        st.markdown("---")
        st.caption("Dashboard Comunidades Regantes generado con Python & Streamlit.")

except Exception as e:
    st.error(f"Se ha producido un error inesperado: {e}")