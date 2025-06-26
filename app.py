# ----------------------------------------------------------
# app.py  |  Relatório RIDE-DF – Internações SUS  (Streamlit)
# ----------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from streamlit_folium import st_folium
import folium

# ---------- CONFIGURAÇÃO GERAL ----------

df = pd.read_csv("")

# ---------- COMPONENTES REUTILIZÁVEIS ----------
def cards_overview(df_f):
    col1, col2 = st.columns(2)
    col1.metric("Total de Internações", f"{df_f['qtd_total'].sum():,}".replace(",", "."))
    col2.metric("Custo Total (R$)", f"{df_f['valor_total'].sum():,.0f}".replace(",", ".").replace(".", ","))

def line_charts(df_f):
    fig_qtd = px.line(df_f.groupby(["ano_aih","mes_label","mes_num"], as_index=False)
                      .agg(qtd_total=("qtd_total","sum")),
                      x="mes_num", y="qtd_total", color="ano_aih",
                      markers=True, title="Evolução Mensal das Internações")
    fig_qtd.update_xaxes(tickvals=df_f["mes_num"].unique(),
                         ticktext=df_f.sort_values("mes_num")["mes_label"].unique())
    st.plotly_chart(fig_qtd, use_container_width=True)

    fig_val = px.line(df_f.groupby(["ano_aih","mes_label","mes_num"], as_index=False)
                      .agg(valor_total=("valor_total","sum")),
                      x="mes_num", y="valor_total", color="ano_aih",
                      markers=True, title="Evolução Mensal dos Custos (R$)")
    fig_val.update_xaxes(tickvals=fig_qtd.layout.xaxis.tickvals,
                         ticktext=fig_qtd.layout.xaxis.ticktext)
    st.plotly_chart(fig_val, use_container_width=True)

def pizza_barras(df_f, medida="qtd_total"):
    # Pizza / Rosca
    pie = px.pie(df_f, names="uf_nome", values=medida,
                 hole=.4, color="uf_nome",
                 title="Distribuição das Internações por UF")
    sel = st.plotly_chart(pie, use_container_width=True)
    # Capturar UF clicada
    click = pie.select_data()
    if click and len(click["points"])>0:
        uf_click = click["points"][0]["label"]
        df_f = df_f[df_f["uf_nome"] == uf_click]

    # Barras horizontal por município
    barras = px.bar(df_f.groupby("nome_municipio", as_index=False)
                        .agg(valor=(medida,"sum"))
                        .sort_values("valor", ascending=False),
                    x="valor", y="nome_municipio",
                    orientation="h", title="Internações por Município")
    st.plotly_chart(barras, use_container_width=True)

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
    pizza_barras(df)

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
