# ----------------------------------------------------------
# app.py  |  Relatório RIDE-DF – Internações SUS  (Streamlit)
# ----------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium
import folium

# ---------- CONFIGURAÇÃO GERAL ----------
st.set_page_config(page_title="Internações SUS – Ride-DF",
                   page_icon="🏥",
                   layout="wide")

# ---------- CARREGAMENTO DO CSV ----------
@st.cache_data(show_spinner="Carregando dados…")
def load_data():
    df = (
        pd.read_csv("sus_ride_df_aih_202506261935.csv")      # ← caminho para o arquivo
          .rename(columns=str.lower)                         # garante minúsculas
    )

    # Mes como int ordenável + label “Jan”, “Fev”…
    df["mes_num"]   = df["mes_aih"].astype(int)
    df["mes_label"] = pd.to_datetime(df["mes_num"], format="%m").dt.strftime("%b")

    return df

df = load_data()


# ---------- COMPONENTES REUTILIZÁVEIS ----------
def cards_overview(df_f):
    col1, col2 = st.columns(2)
    col1.metric("Total de Internações", f"{df_f['qtd_total'].sum():,}".replace(",", "."))
    col2.metric("Custo Total (R$)", f"{df_f['vl_total'].sum():,.0f}".replace(",", ".").replace(".", ","))

def line_charts(df_f):
    # Agrupa e ORDERNA
    qtd = (
        df_f.groupby(["ano_aih", "mes_num"], as_index=False)
            .agg(qtd_total=("qtd_total", "sum"))
            .sort_values(["ano_aih", "mes_num"])          
    )
    fig_qtd = px.line(
        qtd, x="mes_num", y="qtd_total", color="ano_aih",
        markers=True, title="Evolução Mensal das Internações"
    )
    fig_qtd.update_xaxes(
        tickvals=qtd["mes_num"].unique(),
        ticktext=["Jan","Fev","Mar","Abr","Mai","Jun",
                  "Jul","Ago","Set","Out","Nov","Dez"][:len(qtd["mes_num"].unique())]
    )
    st.plotly_chart(fig_qtd, use_container_width=True)

    # ---- gráfico de valores ----
    val = (
        df_f.groupby(["ano_aih", "mes_num"], as_index=False)
            .agg(vl_total=("vl_total", "sum"))
            .sort_values(["ano_aih", "mes_num"])
    )
    fig_val = px.line(
        val, x="mes_num", y="vl_total", color="ano_aih",
        markers=True, title="Evolução Mensal dos Custos (R$)"
    )
    fig_val.update_xaxes(
        tickvals=fig_qtd.layout.xaxis.tickvals,
        ticktext=fig_qtd.layout.xaxis.ticktext
    )
    st.plotly_chart(fig_val, use_container_width=True)

from streamlit_plotly_events import plotly_events
import plotly.express as px
import streamlit as st

def tree_uf_mun(df_f, medida="qtd_total"):
    # --- Treemap ---
    fig = px.treemap(
        df_f,
        path=["uf_nome", "nome_municipio"],
        values=medida,
        color="uf_nome",
        color_discrete_sequence=px.colors.qualitative.Set3,
        title="Internações por UF → Município (clique para detalhar)",
        width=1500,
        height=800
    )
    fig.data[0].textinfo = 'label+percent entry'
    st.plotly_chart(fig, use_container_width=False)

def mapa(df_f):
    m = folium.Map(location=[-15.8,-47.9], zoom_start=6, tiles="CartoDB positron")
    for _,row in df_f.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius = max(row["qtd_total"]/200, 1),  # escala simples
            tooltip=f"{row['nome_municipio']}: {row['qtd_total']} int.",
            color  ="#005DAA" if row["uf_sigla"]=="DF" else "#007F5C" if row["uf_sigla"]=="GO" else "#FF8C00",
            fill=True, fill_opacity=0.7
        ).add_to(m)
    st_folium(m, width=1100, height=600)

# ---------- PÁGINAS ----------
def pagina1():
    st.subheader("Análise Temporal das Internações (Jan/24 – Jan/25)")
    ano_sel = st.radio("Selecione o Ano", sorted(df["ano_aih"].unique()), horizontal=True)
    mun_sel = st.selectbox("Filtrar Município (opcional)",
                           ["Todos"] + sorted(df["nome_municipio"].unique()))
    df_f = df[df["ano_aih"]==ano_sel].copy()
    if mun_sel!="Todos": df_f = df_f[df_f["nome_municipio"]==mun_sel]

    cards_overview(df_f)
    line_charts(df_f)

def pagina2():
    st.subheader("Distribuição por UF e Municípios")
    tree_uf_mun(df)         

def pagina3():
    st.subheader("Mapa – Internações na Ride-DF")
    mapa(df)

# ---------- NAVEGAÇÃO ----------
pagina = st.sidebar.selectbox("Navegue:", ["Página 1 – Temporal",
                                           "Página 2 – Geográfica (UF)",
                                           "Página 3 – Mapa"])

if   pagina.startswith("Página 1"): pagina1()
elif pagina.startswith("Página 2"): pagina2()
else:                               pagina3()
