"""Caso 3 (IDF-MT): constrói o índice, estima os modelos de validação e gera as figuras.

Construção do índice (a mesma da planilha):
  1. cada indicador é normalizado de 0 a 1: (x − mínimo) / (máximo − mínimo);
  2. dimensão = média dos indicadores normalizados × 100;
     digital = banda larga e cobertura 4G; financeira = pontos de atendimento e cooperativa;
     capacidades = escolaridade, capacitação e MEI;
  3. IDF = média das três dimensões (pesos iguais), de 0 a 100.
Uso:  python analise_idf.py   (requer numpy, pandas, statsmodels, matplotlib)
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

BASE = Path(__file__).resolve().parents[1]
INDIC = ["banda_larga", "cobertura_4g", "agencias", "cooperativa", "escolaridade", "capacitacao", "mei_mil"]
NOMES = {"banda_larga": "Banda larga", "cobertura_4g": "Cobertura 4G", "agencias": "Pontos de atendimento",
         "cooperativa": "Cooperativa de crédito", "escolaridade": "Escolaridade", "capacitacao": "Capacitação",
         "mei_mil": "MEI por mil hab."}


def construir_indice(d):
    d = d.copy()
    for c in INDIC:
        d[f"n_{c}"] = (d[c] - d[c].min()) / (d[c].max() - d[c].min())
    d["dim_digital"] = 100 * d[["n_banda_larga", "n_cobertura_4g"]].mean(axis=1)
    d["dim_financeira"] = 100 * d[["n_agencias", "n_cooperativa"]].mean(axis=1)
    d["dim_capacidades"] = 100 * d[["n_escolaridade", "n_capacitacao", "n_mei_mil"]].mean(axis=1)
    d["idf"] = d[["dim_digital", "dim_financeira", "dim_capacidades"]].mean(axis=1)
    return d


df = construir_indice(pd.read_csv(BASE / "dados" / "idf_mt.csv"))
df["lpix"] = np.log(df["pix_pj"])
df["lpop"] = np.log(df["pop"])
df["lpib"] = np.log(df["pib_pc"])
for m in ["Nordeste", "Sudoeste", "Centro-Sul", "Sudeste"]:
    df["m_" + m.lower().replace("-", "_")] = (df["mesorregiao"] == m).astype(int)

specs = {
    "I1": "lpix ~ idf",
    "I2": "lpix ~ idf + lpop + lpib",
    "I3": "lpix ~ dim_digital + dim_financeira + dim_capacidades + lpop + lpib",
    "I4": "lpix ~ " + " + ".join(INDIC) + " + lpop + lpib",
}
out = {}
for k, f in specs.items():
    m = smf.ols(f, data=df).fit()
    r = m.get_robustcov_results("HC1")
    out[k] = {"formula": f, "n": int(m.nobs), "r2": m.rsquared, "r2a": m.rsquared_adj,
              "coef": dict(zip(m.params.index, m.params.values)),
              "ep_hc1": dict(zip(m.params.index, r.bse)),
              "ep_classico": dict(zip(m.bse.index, m.bse.values)),
              "p_hc1": dict(zip(m.params.index, r.pvalues))}

# Consistência interna: alfa de Cronbach dos 7 indicadores normalizados
Z = df[[f"n_{c}" for c in INDIC]]
k = Z.shape[1]
out["alfa_cronbach"] = float(k / (k - 1) * (1 - Z.var(ddof=1).sum() / Z.sum(axis=1).var(ddof=1)))
out["corr_idf_lpop"] = float(df[["idf", "lpop"]].corr().iloc[0, 1])
out["corr_idf_lpib"] = float(df[["idf", "lpib"]].corr().iloc[0, 1])
out["corr_idf_lpix"] = float(df[["idf", "lpix"]].corr().iloc[0, 1])
out["idf_resumo"] = df["idf"].describe().round(2).to_dict()
out["idf_meso"] = df.groupby("mesorregiao")["idf"].mean().round(1).to_dict()
top = df.sort_values("idf", ascending=False)
out["top5"] = top[["municipio", "idf", "pop"]].head(5).round(1).to_dict("records")
out["bottom5"] = top[["municipio", "idf", "pop"]].tail(5).round(1).to_dict("records")

# Efeito de ir do pior ao melhor município em cada indicador (modelo I4)
c4 = out["I4"]["coef"]
e4 = out["I4"]["ep_hc1"]
efeito = {}
for c in INDIC:
    amp = df[c].max() - df[c].min()
    efeito[c] = {"amplitude": float(amp), "efeito_pct": 100 * (np.exp(c4[c] * amp) - 1),
                 "li": 100 * (np.exp((c4[c] - 1.96 * e4[c]) * amp) - 1),
                 "ls": 100 * (np.exp((c4[c] + 1.96 * e4[c]) * amp) - 1),
                 "p": out["I4"]["p_hc1"][c]}
out["efeito_amplitude"] = efeito
verdade = {"banda_larga": 0.012, "cobertura_4g": 0, "agencias": 0, "cooperativa": 0.30,
           "escolaridade": 0, "capacitacao": 0.004, "mei_mil": 0}
out["efeito_verdadeiro_pct"] = {c: 100 * (np.exp(verdade[c] * efeito[c]["amplitude"]) - 1) for c in INDIC}
(BASE / "codigo" / "resultados_idf.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

# =============================================================================
# Figuras
# =============================================================================
AZUL, LARANJA, TINTA, CINZA = "#1866a3", "#b5562a", "#1d2330", "#8a909c"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": CINZA, "axes.grid": True,
                     "grid.color": "#e6e3dc", "grid.linewidth": 0.8, "figure.facecolor": "white"})


def virgula(v, _):
    return f"{v:.2f}".rstrip("0").rstrip(".").replace("-", "−").replace(".", ",")


def salvar(fig, nome):
    for ax in fig.axes:
        for eixo in (ax.xaxis, ax.yaxis):
            if isinstance(eixo.get_major_formatter(), matplotlib.ticker.ScalarFormatter):
                eixo.set_major_formatter(matplotlib.ticker.FuncFormatter(virgula))
    fig.tight_layout()
    fig.savefig(BASE / "img" / nome, dpi=160)
    plt.close(fig)


# Figura 7: índice × uso de Pix, tamanho do ponto = população
fig, ax = plt.subplots(figsize=(8.6, 4.8))
tam = 10 + 140 * (df["pop"] / df["pop"].max()) ** 0.6
ax.scatter(df["idf"], df["pix_pj"], s=tam, color=AZUL, alpha=0.55, linewidths=0, zorder=2)
xs = np.linspace(df.idf.min(), df.idf.max(), 50)
b = out["I1"]["coef"]
ax.plot(xs, np.exp(b["Intercept"] + b["idf"] * xs), color=LARANJA, lw=2.2, zorder=3)
ax.set_xlabel("IDF-MT (0 a 100)")
ax.set_ylabel("Pix recebidos por empresa por mês")
ax.set_title("Mais condições, mais Pix (bolhas maiores = municípios maiores)", loc="left", fontsize=12.5)
salvar(fig, "fig7_idf_pix.png")

# Figura 8: efeito de ir do pior ao melhor município, por indicador
ordem = sorted(INDIC, key=lambda c: efeito[c]["efeito_pct"])
fig, ax = plt.subplots(figsize=(8.6, 4.8))
y = np.arange(len(ordem))
est = [efeito[c]["efeito_pct"] for c in ordem]
li = [efeito[c]["li"] for c in ordem]
ls = [efeito[c]["ls"] for c in ordem]
ax.hlines(y, li, ls, color=AZUL, lw=2, zorder=2)
ax.plot(est, y, "o", color=AZUL, ms=8, zorder=3, label="estimado (IC 95%)")
ax.plot([out["efeito_verdadeiro_pct"][c] for c in ordem], y, "D", mfc="white", mec=LARANJA,
        mew=2, ms=8, zorder=4, label="verdadeiro")
ax.axvline(0, color=TINTA, lw=1)
ax.set_yticks(y, [NOMES[c] for c in ordem])
ax.set_xlabel("Mudança no Pix por empresa (%) indo do pior ao melhor município")
ax.legend(frameon=False, loc="lower right", fontsize=10)
ax.grid(axis="y", visible=False)
ax.set_title("Nem todo indicador do índice faz diferença", loc="left", fontsize=13)
salvar(fig, "fig8_idf_indicadores.png")

for kk in specs:
    o = out[kk]
    print(kk, f"R2={o['r2']:.3f}", {a: (round(o['coef'][a], 4), round(o['ep_hc1'][a], 4), round(o['p_hc1'][a], 3))
                                    for a in o["coef"] if a != "Intercept"})
print("alfa", round(out["alfa_cronbach"], 3), "corr", round(out["corr_idf_lpop"], 2), round(out["corr_idf_lpib"], 2),
      round(out["corr_idf_lpix"], 2))
print({c: (round(v["efeito_pct"], 1), round(v["li"], 1), round(v["ls"], 1)) for c, v in efeito.items()})
print({c: round(v, 1) for c, v in out["efeito_verdadeiro_pct"].items()})
print(out["idf_meso"], out["idf_resumo"])
