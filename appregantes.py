# streamlit run appregantes.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Monitor Avance | Comunidades Regantes",
    page_icon="💧",
    layout="wide"
)

# --- 2. PALETA DE COLORES ACUÁTICOS ---
C_AQUA      = '#00B4D8' 
C_TEAL      = '#0077B6' 
C_TURQUOISE = '#48CAE4' 
C_GREEN     = '#20B2AA' 
C_LIGHT     = '#90E0EF' 
C_DARK_TEXT = '#1A365D' 

PALETTE_AGUA = [C_AQUA, C_TEAL, C_GREEN, C_TURQUOISE, C_LIGHT]

# --- 3. ESTILOS CSS PERSONALIZADOS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F4F9F9 !important; color: {C_DARK_TEXT} !important; }}
    h1, h2, h3 {{ color: {C_DARK_TEXT} !important; border-left: 5px solid {C_AQUA} !important; padding-left: 15px !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
    div[data-testid="stMetric"] {{ background-color: #FFFFFF !important; border: 1px solid #E0F2F1 !important; padding: 20px !important; border-radius: 10px; box-shadow: 0 4px 10px rgba(0, 119, 182, 0.05); text-align: center; min-height: 160px; display: flex; flex-direction: column; justify-content: center; }}
    [data-testid="stMetricLabel"] {{ color: #5F7A8C !important; font-size: 1.1rem !important; font-weight: 600 !important; text-transform: uppercase; }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{ color: {C_AQUA} !important; font-size: 45px !important; font-weight: 800 !important; line-height: 1.2 !important; }}
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stVerticalBlock"] {{ background-color: #FFFFFF !important; border: 1px solid #E0F2F1 !important; border-radius: 10px; box-shadow: 0 4px 10px rgba(0, 119, 182, 0.05); padding: 10px; height: 160px; display: flex; align-items: center; justify-content: center; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def load_data():
    file_name = 'results-survey959375.csv' 
    try:
        df = pd.read_csv(file_name, sep=';', encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_name, sep=',', encoding='utf-8')
        except:
            return None

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
    
    cols_categoricas = ['Provincia', 'Demarcación Hidrográfica', 'Nombre de la Comunidad de Regantes (CC.RR.)']
    for col in cols_categoricas:
        if col in df.columns:
            df[col] = df[col].fillna("Sin especificar")

    cols_numericas = ['Número de comuneros', 'Superficie total del área de riego en Has.']
    for col in cols_numericas:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'Fecha' in df.columns:
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], format='%d-%m-%Y', errors='coerce')
        df['Fecha_dt'] = df['Fecha_dt'].fillna(pd.Timestamp.today())
        
    return df

# --- 5. FUNCIÓN CREADORA DE DASHBOARDS ---
def generar_dashboard(df_vista, meta_objetivo, mostrar_demarcacion=True):
    total_real = len(df_vista) 
    pct_avance = min((total_real / meta_objetivo) * 100, 100) if meta_objetivo > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Respuestas Registradas", total_real) 
    c2.metric("Meta Objetivo", meta_objetivo)
    c3.metric("Faltantes", max(0, meta_objetivo - total_real))
    
    with c4:
        fig_g = go.Figure(go.Indicator(
            domain={'x': [0, 1], 'y': [0, 1]}, 
            mode = "gauge+number", value = pct_avance,
            title = {'text': "AVANCE GLOBAL", 'font': {'size': 12, 'color': C_DARK_TEXT}},
            number = {'suffix': "%", 'font': {'size': 26, 'color': C_AQUA, 'weight': 'bold'}}, # Letra un pelín más pequeña
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 0, 'tickcolor': "white"},
                'bar': {'color': C_AQUA},
                'bgcolor': "#E0F2F1",
                'borderwidth': 0,
                'bordercolor': "white"
            }
        ))
        
        # EL TRUCO: Darle un ancho y alto fijo para que no se deforme al estar en una pestaña oculta
        fig_g.update_layout(
            width=300,   # <--- Ancho fijo en píxeles
            height=200,  # <--- Alto fijo en píxeles
            margin=dict(t=30, b=10, l=20, r=30), 
            paper_bgcolor='rgba(0,0,0,0)', 
            font={'family': "Arial"}
        )
        
        # Apagamos el use_container_width para que respete nuestras medidas exactas
        st.plotly_chart(fig_g, use_container_width=False)

    st.markdown("---")

    def aplicar_estilo(fig, mt=30):
        fig.update_layout(
            paper_bgcolor='white', plot_bgcolor='white', font={'color': C_DARK_TEXT, 'size': 14}, 
            margin=dict(l=20, r=50, t=mt, b=20), showlegend=False
        )
        fig.update_xaxes(showline=True, linewidth=1, linecolor='#B2EBF2', gridcolor='#E0F2F1', zeroline=False)
        fig.update_yaxes(showline=True, linewidth=1, linecolor='#B2EBF2', gridcolor='#E0F2F1', zeroline=False)
        return fig

    st.markdown("### Dinámica de Registro")
    g1, g2 = st.columns((2, 1))
    
    with g1:
        st.markdown(f"**<span style='color:{C_TEAL}'>📅 Evolución Diaria de Registros</span>**", unsafe_allow_html=True)
        
        if 'Fecha_dt' in df_vista.columns and not df_vista.empty:
            # 1. Agrupamos por el objeto datetime real (sin formatear a string todavía)
            diario = df_vista.groupby('Fecha_dt').size().reset_index(name='N')
            
            # 2. Ordenamos cronológicamente de forma explícita
            diario = diario.sort_values('Fecha_dt')
            
            # 3. Graficamos usando la columna datetime
            fig1 = px.line(diario, x='Fecha_dt', y='N', markers=True, text='N')
            
            # 4. TRUCO: Le decimos a Plotly que use formato dd-mm-yyyy solo para mostrarlo
            fig1.update_xaxes(
                type='date',           # Asegura que sea un eje de tiempo
                tickformat="%d-%m-%Y", # Formato visual en el eje
                dtick="D1",            # (Opcional) Fuerza una marca por cada día
                title_text='Fecha'
            )
            
            fig1.update_traces(
                line_color=C_TEAL, 
                marker_color=C_AQUA, 
                line_width=3, 
                marker_size=10, 
                textposition="top center", 
                textfont_size=16
            )
            
            fig1 = aplicar_estilo(fig1)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sin datos suficientes de fecha.")
            
    with g2:
        st.markdown(f"**<span style='color:{C_TEAL}'>📍 Registros por Provincia</span>**", unsafe_allow_html=True)
        if 'Provincia' in df_vista.columns and not df_vista.empty:
            prov = df_vista['Provincia'].value_counts().head(5).reset_index()
            prov.columns = ['Provincia', 'N']
            fig2 = px.bar(prov, x='Provincia', y='N', text='N', color_discrete_sequence=[C_DARK_TEXT])
            fig2.update_traces(textposition='outside')
            fig2 = aplicar_estilo(fig2, mt=25) 
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Perfil de las Comunidades de Regantes")
    
    if mostrar_demarcacion:
        g3, g4 = st.columns(2)
        with g3:
            st.markdown(f"**<span style='color:{C_TEAL}'>Demarcación Hidrográfica</span>**", unsafe_allow_html=True)
            if 'Demarcación Hidrográfica' in df_vista.columns and not df_vista.empty:
                dem = df_vista['Demarcación Hidrográfica'].value_counts().reset_index()
                dem.columns = ['Demarcación', 'N']
                fig3 = px.pie(dem, values='N', names='Demarcación', hole=0.5, color_discrete_sequence=PALETTE_AGUA)
                fig3.update_layout(paper_bgcolor='white', font={'color': C_DARK_TEXT, 'size': 16}, margin=dict(l=20, r=50, t=30, b=20), legend=dict(orientation="h", y=-0.2, font=dict(size=12)))
                st.plotly_chart(fig3, use_container_width=True)
                
        with g4:
            st.markdown(f"**<span style='color:{C_TEAL}'>Top 5 Superficie total Área de Riego (Has.)</span>**", unsafe_allow_html=True)
            if 'Superficie total del área de riego en Has.' in df_vista.columns and not df_vista.empty:
                sup = df_vista.nlargest(5, 'Superficie total del área de riego en Has.')[['Nombre de la Comunidad de Regantes (CC.RR.)', 'Superficie total del área de riego en Has.']]
                sup.columns = ['CC.RR.', 'Hectáreas']
                if sup['Hectáreas'].sum() > 0:
                    fig4 = px.bar(sup, y='CC.RR.', x='Hectáreas', orientation='h', text='Hectáreas', color_discrete_sequence=[C_AQUA])
                    fig4.update_traces(textposition='inside', textfont_color='white')
                    fig4 = aplicar_estilo(fig4)
                    fig4.update_yaxes(autorange="reversed") 
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Sin datos de superficie introducidos.")
    else:
        st.markdown(f"**<span style='color:{C_TEAL}'>Top 5 Superficie total Área de Riego (Has.)</span>**", unsafe_allow_html=True)
        if 'Superficie total del área de riego en Has.' in df_vista.columns and not df_vista.empty:
            sup = df_vista.nlargest(5, 'Superficie total del área de riego en Has.')[['Nombre de la Comunidad de Regantes (CC.RR.)', 'Superficie total del área de riego en Has.']]
            sup.columns = ['CC.RR.', 'Hectáreas']
            if sup['Hectáreas'].sum() > 0:
                fig4 = px.bar(sup, y='CC.RR.', x='Hectáreas', orientation='h', text='Hectáreas', color_discrete_sequence=[C_AQUA])
                fig4.update_traces(textposition='inside', textfont_color='white')
                fig4 = aplicar_estilo(fig4)
                fig4.update_yaxes(autorange="reversed") 
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Sin datos de superficie introducidos.")

    st.markdown(f"### Comunidades con Mayor Número de Comuneros")
    if 'Número de comuneros' in df_vista.columns and not df_vista.empty:
        comuneros = df_vista.nlargest(15, 'Número de comuneros')[['Nombre de la Comunidad de Regantes (CC.RR.)', 'Número de comuneros']]
        comuneros.columns = ['CC.RR.', 'Comuneros']
        if comuneros['Comuneros'].sum() > 0:
            fig5 = px.bar(comuneros, x='CC.RR.', y='Comuneros', text='Comuneros', color_discrete_sequence=[C_GREEN])
            fig5.update_traces(textposition='outside', cliponaxis=False)
            fig5 = aplicar_estilo(fig5)
            fig5.update_layout(height=600, margin=dict(t=40, b=150, l=20, r=20))
            fig5.update_xaxes(tickangle=-45)
            st.plotly_chart(fig5, use_container_width=True)
        else:
             st.info("Sin datos de comuneros introducidos.")


# --- 6. LÓGICA PRINCIPAL Y PESTAÑAS ---
try:
    df = load_data()
    
    if df is None:
        st.error("⚠️ No se pudo leer el archivo 'results-survey959375.csv'. Verifica que el nombre sea correcto.")
    else:
        # --- CABECERA (Logo + Título) ---
        col_logo, col_titulo = st.columns([1, 5])
        with col_logo:
            st.image("logo.png", use_container_width=True)
        with col_titulo:
            st.markdown(f"<h1>Monitor de Avance | <span style='color:{C_AQUA}'>Comunidades de Regantes</span></h1>", unsafe_allow_html=True)
            st.markdown("Visión general del registro y caracterización de las Comunidades de Regantes.")
        st.markdown("<br>", unsafe_allow_html=True)

        # --- CREACIÓN DE LAS 3 PESTAÑAS ---
        tab1, tab2, tab3 = st.tabs(["📊 Visión General", "💧 D.H. Guadalquivir", "🌊 D.H. Cuencas Mediterráneas"])

        with tab1:
            st.subheader("Panorama General de Encuestas")
            # Usamos el dataframe completo
            generar_dashboard(df, meta_objetivo=106, mostrar_demarcacion=True)

        with tab2:
            st.subheader("Campaña Enfocada: D.H. Guadalquivir")
            df_guadalquivir = df[df['Demarcación Hidrográfica'].str.contains('Guadalquivir', case=False, na=False)]
            generar_dashboard(df_guadalquivir, meta_objetivo=30, mostrar_demarcacion=False)

        with tab3:
            st.subheader("Campaña Enfocada: D.H. Cuencas Mediterráneas Andaluzas")
            df_mediterraneo = df[df['Demarcación Hidrográfica'].str.contains('Mediterránea', case=False, na=False)]
            generar_dashboard(df_mediterraneo, meta_objetivo=30, mostrar_demarcacion=False)

        st.markdown("---")
        st.caption("Dashboard Comunidades Regantes generado con Python & Streamlit. Propiedad de CITERE.")

except Exception as e:
    st.error(f"Se ha producido un error inesperado: {e}")