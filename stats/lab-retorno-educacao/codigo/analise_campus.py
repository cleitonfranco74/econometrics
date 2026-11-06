"""Gabarito do Exemplo 2 (campus federal e renda municipal): modelos e figuras.

Uso:  python analise_campus.py   (requer numpy, pandas, statsmodels, matplotlib)
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
df = pd.read_csv(BASE / "dados" / "municipios_campus.csv")
df["lrenda10"] = np.log(df["renda_pc_2010"])
df["lrenda00"] = np.log(df["renda_pc_2000"])
df["lpop"] = np.log(df["pop_2000"])
df["dlrenda"] = df["lrenda10"] - df["lrenda00"]
df["campus_pequeno"] = df["campus"] * df["pequeno"]
df["dist100"] = df["dist_capital"] / 100        # centenas de km

AZUL, LARANJA, TINTA, CINZA = "#1866a3", "#b5562a", "#1d2330", "#8a909c"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": CINZA, "axes.grid": True, "grid.color": "#e6e3dc",
                     "grid.linewidth": 0.8, "figure.facecolor": "white"})

ctrl = "lpop + urbanizacao_2000 + dist100 + norte + nordeste + sul + centro_oeste"
specs = {
    "C1": "lrenda10 ~ campus",
    "C2": "lrenda10 ~ campus + lrenda00",
    "C3": f"lrenda10 ~ campus + lrenda00 + {ctrl}",
    "C4": f"lrenda10 ~ campus + campus_pequeno + pequeno + lrenda00 + {ctrl}",
    "C5": "dlrenda ~ campus",
    "C6": f"dlrenda ~ campus + {ctrl}",
    "P1": "pobreza_2010 ~ campus",
    "P2": f"pobreza_2010 ~ campus + pobreza_2000 + lrenda00 + {ctrl}",
    "S1": "campus ~ lpop + lrenda00 + dist100",
}
out = {}
for nome, f in specs.items():
    m = smf.ols(f, data=df).fit()
    r = m.get_robustcov_results("HC1")
    out[nome] = {"formula": f, "n": int(m.nobs), "r2": m.rsquared, "r2a": m.rsquared_adj,
                 "coef": dict(zip(m.params.index, m.params.values)),
                 "ep_hc1": dict(zip(m.params.index, r.bse)),
                 "ep_classico": dict(zip(m.bse.index, m.bse.values)),
                 "p_hc1": dict(zip(m.params.index, r.pvalues))}

out["n_campus"] = int(df["campus"].sum())
out["pct_pequeno_campus"] = float(df.loc[df.campus == 1, "pequeno"].mean())
out["efeito_verdadeiro_medio_tratados"] = 0.035 + 0.035 * out["pct_pequeno_campus"]
out["medianas"] = df.groupby("campus")[["pop_2000", "renda_pc_2000", "renda_pc_2010",
                                        "dist_capital", "urbanizacao_2000", "pobreza_2000",
                                        "pobreza_2010"]].median().round(2).to_dict("index")
out["medias"] = df.groupby("campus")[["lrenda00", "lrenda10", "dlrenda", "lpop"]].mean().to_dict("index")
c4 = out["C4"]["coef"]
out["efeito_pequeno_C4"] = c4["campus"] + c4["campus_pequeno"]
(BASE / "codigo" / "resultados_campus.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")


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


# Figura 5: quem recebeu campus já era diferente antes
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
for g, cor, rot, z in ((0, CINZA, "sem campus", 2), (1, LARANJA, "com campus novo", 3)):
    d = df[df.campus == g]
    axs[0].scatter(d["pop_2000"] / 1000, d["renda_pc_2000"], s=12 if g else 7,
                   alpha=0.85 if g else 0.35, color=cor, label=rot, zorder=z, linewidths=0)
axs[0].set_xscale("log")
axs[0].xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
axs[0].set_xlabel("População em 2000 (mil, escala log)")
axs[0].set_ylabel("Renda per capita em 2000 (R$)")
axs[0].set_title("Antes: campi foram para cidades maiores e mais ricas", loc="left", fontsize=12)
axs[0].legend(frameon=False, loc="upper left", fontsize=10, markerscale=1.6)
for g, cor, rot, z in ((0, CINZA, "sem campus", 2), (1, LARANJA, "com campus novo", 3)):
    d = df[df.campus == g]
    axs[1].scatter(d["lrenda00"], d["lrenda10"], s=12 if g else 7, alpha=0.85 if g else 0.35,
                   color=cor, label=rot, zorder=z, linewidths=0)
xs = np.linspace(df.lrenda00.min(), df.lrenda00.max(), 20)
c2 = out["C2"]["coef"]
axs[1].plot(xs, c2["Intercept"] + c2["lrenda00"] * xs, color=CINZA, lw=1.8, zorder=4)
axs[1].plot(xs, c2["Intercept"] + c2["campus"] + c2["lrenda00"] * xs, color=LARANJA, lw=1.8, zorder=4)
axs[1].set_xlabel("ln(renda per capita 2000)")
axs[1].set_ylabel("ln(renda per capita 2010)")
axs[1].set_title("Depois: a mesma renda inicial, um pouco mais de renda", loc="left", fontsize=12)
salvar(fig, "fig5_campus_selecao.png")

# Figura 6: caminho do coeficiente de campus
nomes = ["(C1) só campus", "(C2) + renda de 2000", "(C3) + população, região...",
         "(C5) variação da renda", "(C6) variação + controles"]
mods = ["C1", "C2", "C3", "C5", "C6"]
coefs = [out[m]["coef"]["campus"] for m in mods]
eps = [out[m]["ep_hc1"]["campus"] for m in mods]
fig, ax = plt.subplots(figsize=(8.6, 4.2))
y = np.arange(len(nomes))[::-1]
ax.errorbar(coefs, y, xerr=1.96 * np.array(eps), fmt="o", color=AZUL, ms=8, ecolor=AZUL,
            elinewidth=2, capsize=0, zorder=3)
v = out["efeito_verdadeiro_medio_tratados"]
ax.axvline(v, color=LARANJA, lw=1.6, ls="--", zorder=2)
ax.text(v, len(nomes) - 0.35, f" verdadeiro: {v:.3f}".replace(".", ","), color=LARANJA, fontsize=11, va="bottom")
for c, yy in zip(coefs, y):
    ax.text(c, yy + 0.18, f"{c:.3f}".replace(".", ","), ha="center", fontsize=10.5, color=TINTA)
ax.set_yticks(y, nomes)
ax.set_ylim(-0.6, len(nomes) - 0.1)
ax.set_xlabel("Coeficiente de campus (IC 95%, EP robusto)")
ax.grid(axis="y", visible=False)
ax.set_title("O “efeito” do campus depende do que se compara", loc="left", fontsize=13)
salvar(fig, "fig6_campus_coeficiente.png")

for k in mods + ["C4", "P1", "P2", "S1"]:
    o = out[k]
    print(k, f"R2={o['r2']:.3f}", {a: (round(o['coef'][a], 4), round(o['ep_hc1'][a], 4), round(o['p_hc1'][a], 3))
                                   for a in o["coef"] if a != "Intercept"})
print("verdadeiro", v, "pequeno C4", out["efeito_pequeno_C4"], out["medianas"])
