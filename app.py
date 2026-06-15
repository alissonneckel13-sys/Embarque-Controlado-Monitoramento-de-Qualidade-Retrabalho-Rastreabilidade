import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Embarque Controlado", layout="wide")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0f172a,#1e293b);}
h1,h2,h3{color:white !important;}
[data-testid="stMetric"]{
background:#1E293B;border:1px solid #334155;padding:18px;
border-radius:16px;box-shadow:0 4px 15px rgba(0,0,0,0.30);}
[data-testid="stMetricValue"]{color:white;}
[data-testid="stMetricLabel"]{color:#CBD5E1;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style='text-align:center;'>🚚 Embarque Controlado</h1>
<p style='text-align:center;color:#94A3B8;'>
Monitoramento de Qualidade • Retrabalho • Rastreabilidade
</p>
""", unsafe_allow_html=True)

URL = "https://docs.google.com/spreadsheets/d/1YfWO4Oa9fXF_bS7PS2NgRPUs1mrH8FIU8_kY4ANtkyI/export?format=csv&gid=0"

@st.cache_data(ttl=10)
def load_data():
    df = pd.read_csv(URL)
    df.columns = df.columns.str.strip().str.upper()
    if "HORAS RETRABALHO" in df.columns:
        df["HORAS RETRABALHO"] = pd.to_numeric(df["HORAS RETRABALHO"], errors="coerce").fillna(0)
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], dayfirst=True, errors="coerce")
    return df

df = load_data()

st.sidebar.header("Filtros")

if "MODELO" in df.columns:
    modelos = st.sidebar.multiselect("Modelo", sorted(df["MODELO"].dropna().unique()))
    if modelos:
        df = df[df["MODELO"].isin(modelos)]

if "OBSERVAÇÃO" in df.columns:
    setores = st.sidebar.multiselect("Observação", sorted(df["OBSERVAÇÃO"].dropna().unique()))
    if setores:
        df = df[df["OBSERVAÇÃO"].isin(setores)]

total_horas = df["HORAS RETRABALHO"].sum()
total_registros = len(df)
total_maquinas = df["NÚMERO DE SÉRIE"].nunique()
total_erros = (df["SETOR CAUSADOR"].astype(str).str.upper() != "OK").sum()

c1,c2,c3,c4 = st.columns(4)
c1.metric("⏱ Horas Retrabalho", f"{total_horas:.2f}")
c2.metric("📊 Registros", total_registros)
c3.metric("🔍 Máquinas", total_maquinas)
c4.metric("❌ Erros", total_erros)

st.markdown("---")

cc1,cc2,cc3 = st.columns(3)

try:
    defeito_top = df[df["SETOR CAUSADOR"]!="OK"]["SETOR CAUSADOR"].value_counts().idxmax()
except:
    defeito_top = "-"

try:
    maquina_top = df.groupby("MODELO")["HORAS RETRABALHO"].sum().idxmax()
except:
    maquina_top = "-"

try:
    setor_top = df["OBSERVAÇÃO"].value_counts().idxmax()
except:
    setor_top = "-"

cc1.success(f"🔥 Defeito mais recorrente\n\n{defeito_top}")
cc2.warning(f"⚠️ Modelo mais crítico\n\n{maquina_top}")
cc3.info(f"🏭 Setor mais afetado\n\n{setor_top}")

qualidade = max(0, round(100 - ((total_erros/max(total_registros,1))*100),1))

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=qualidade,
    title={"text":"Índice de Qualidade (%)"},
    gauge={
        "axis":{"range":[0,100]},
        "bar":{"color":"#10B981"},
        "steps":[
            {"range":[0,60],"color":"#DC2626"},
            {"range":[60,80],"color":"#F59E0B"},
            {"range":[80,100],"color":"#10B981"}
        ]
    }
))
st.plotly_chart(fig_gauge, use_container_width=True)

colA,colB = st.columns(2)

with colA:
    st.subheader("🎯 Pareto 80/20")

    pareto = df.groupby("SETOR CAUSADOR")["HORAS RETRABALHO"].sum().reset_index()
    pareto = pareto.sort_values("HORAS RETRABALHO", ascending=False)
    pareto["ACUMULADO"] = (pareto["HORAS RETRABALHO"].cumsum()/pareto["HORAS RETRABALHO"].sum())*100

    fig = go.Figure()
    fig.add_bar(x=pareto["SETOR CAUSADOR"], y=pareto["HORAS RETRABALHO"], name="Horas")
    fig.add_scatter(x=pareto["SETOR CAUSADOR"], y=pareto["ACUMULADO"],
                    yaxis="y2", mode="lines+markers", name="% Acumulado")
    fig.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font_color="white",
        yaxis2=dict(overlaying="y", side="right", range=[0,100])
    )
    st.plotly_chart(fig, use_container_width=True)

with colB:
    st.subheader("🧠 Ranking Inteligente")

    freq = df["SETOR CAUSADOR"].value_counts()

    ranking = df.groupby("SETOR CAUSADOR")["HORAS RETRABALHO"].sum().reset_index()
    ranking["FREQUENCIA"] = ranking["SETOR CAUSADOR"].map(freq)
    ranking["SCORE IA"] = ranking["HORAS RETRABALHO"] * np.log1p(ranking["FREQUENCIA"])
    ranking = ranking.sort_values("SCORE IA", ascending=False)

    fig2 = px.bar(
        ranking,
        y="SETOR CAUSADOR",
        x="SCORE IA",
        orientation="h",
        color="SCORE IA",
        color_continuous_scale="Blues"
    )
    fig2.update_layout(
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font_color="white"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("📈 Evolução do Retrabalho")

evolucao = df.groupby("DATA")["HORAS RETRABALHO"].sum().reset_index()

fig3 = px.line(evolucao, x="DATA", y="HORAS RETRABALHO", markers=True)
fig3.update_layout(
    paper_bgcolor="#1E293B",
    plot_bgcolor="#1E293B",
    font_color="white"
)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("🏆 Ranking de Máquinas")

rank = df.groupby("MODELO")["HORAS RETRABALHO"].sum().reset_index()
rank = rank.sort_values("HORAS RETRABALHO", ascending=False)

fig4 = px.bar(
    rank,
    y="MODELO",
    x="HORAS RETRABALHO",
    orientation="h",
    color="HORAS RETRABALHO",
    color_continuous_scale="Reds"
)
fig4.update_layout(
    paper_bgcolor="#1E293B",
    plot_bgcolor="#1E293B",
    font_color="white"
)
st.plotly_chart(fig4, use_container_width=True)

st.subheader("🔥 Heatmap Máquina x Defeito")

heat = pd.crosstab(df["MODELO"], df["SETOR CAUSADOR"])

fig5 = px.imshow(heat, aspect="auto", text_auto=True)
fig5.update_layout(
    paper_bgcolor="#1E293B",
    plot_bgcolor="#1E293B",
    font_color="white"
)
st.plotly_chart(fig5, use_container_width=True)

st.subheader("📋 Dados MES")
st.dataframe(df, use_container_width=True)

st.caption("Atualização automática a cada 10 segundos")
