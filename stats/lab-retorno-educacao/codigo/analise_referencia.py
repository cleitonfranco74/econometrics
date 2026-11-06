"""Gabarito do Laboratório: estima todos os modelos e gera as figuras.

Serve para conferir os resultados que os alunos obtêm no Gretl e no Excel.
Uso:  python analise_referencia.py   (requer numpy, pandas, statsmodels, matplotlib)
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
from statsmodels.stats.diagnostic import het_white
from statsmodels.stats.outliers_influence import variance_inflation_factor

BASE = Path(__file__).resolve().parents[1]
IMG = BASE / "img"
IMG.mkdir(exist_ok=True)
df = pd.read_csv(BASE / "dados" / "pnad_simulada.csv")
df["lsal"] = np.log(df["salario_hora"])
df["exper2"] = df["exper"] ** 2
df["educ_mulher"] = df["educ"] * df["mulher"]

AZUL, LARANJA, TINTA, CINZA = "#1866a3", "#b5562a", "#1d2330", "#8a909c"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": CINZA, "axes.labelcolor": TINTA,
                     "xtick.color": TINTA, "ytick.color": TINTA,
                     "axes.grid": True, "grid.color": "#e6e3dc", "grid.linewidth": 0.8,
                     "figure.facecolor": "white", "axes.facecolor": "white"})

out = {}


def reg(nome, formula, dados=df):
    m = smf.ols(formula, data=dados).fit()
    r = m.get_robustcov_results(cov_type="HC1")
    out[nome] = {
        "formula": formula, "n": int(m.nobs), "r2": m.rsquared, "r2a": m.rsquared_adj,
        "coef": dict(zip(m.params.index, m.params.values)),
        "ep_classico": dict(zip(m.bse.index, m.bse.values)),
        "ep_hc1": dict(zip(m.params.index, r.bse)),
        "p_hc1": dict(zip(m.params.index, r.pvalues)),
        "sigma": float(np.sqrt(m.scale)),
    }
    return m


# --- Descritivas -------------------------------------------------------------
ordem = ["Fund. incompleto", "Fundamental", "Médio", "Superior"]
desc = df.groupby("nivel").agg(n=("id", "size"), sal_hora=("salario_hora", "mean"),
                               sal_med=("salario_hora", "median"),
                               renda=("renda_mensal", "mean")).loc[ordem]
out["descritivas_nivel"] = desc.round(2).reset_index().to_dict("records")
out["premio_sup_medio_media"] = desc.loc["Superior", "sal_hora"] / desc.loc["Médio", "sal_hora"] - 1
out["premio_sup_medio_mediana"] = desc.loc["Superior", "sal_med"] / desc.loc["Médio", "sal_med"] - 1
out["resumo"] = df[["salario_hora", "renda_mensal", "educ", "exper", "idade", "horas",
                    "mulher", "urbano", "superior", "educ_mae"]].describe().T.round(3).to_dict("index")
out["corr_educ_habilidade"] = float(df[["educ", "habilidade"]].corr().iloc[0, 1])
out["corr_educ_lsal"] = float(df[["educ", "lsal"]].corr().iloc[0, 1])

# --- Regressão simples -------------------------------------------------------
s1 = reg("S1_nivel", "salario_hora ~ educ")
s2 = reg("S2_log", "lsal ~ educ")
s3 = reg("S3_dummy", "lsal ~ superior")
sub = df[df["nivel"].isin(["Médio", "Superior"])]
s4 = reg("S4_dummy_med_sup", "lsal ~ superior", sub)
s5 = reg("S5_nivel_dummy", "salario_hora ~ superior", sub)

# --- Regressão múltipla ------------------------------------------------------
m1 = reg("M1", "lsal ~ educ + exper + exper2 + mulher")
m2 = reg("M2", "lsal ~ educ + exper + exper2 + mulher + norte + nordeste + sul + centro_oeste + urbano")
m3 = reg("M3", "lsal ~ educ + superior + exper + exper2 + mulher + norte + nordeste + sul + centro_oeste + urbano")
m4 = reg("M4", "lsal ~ educ + superior + exper + exper2 + mulher + norte + nordeste + sul + centro_oeste + urbano + habilidade")
m5 = reg("M5", "lsal ~ educ + superior + exper + exper2 + mulher + educ_mulher + norte + nordeste + sul + centro_oeste + urbano + habilidade")
m6 = reg("M6_niveis", "lsal ~ fundamental + medio + superior + exper + exper2 + mulher + norte + nordeste + sul + centro_oeste + urbano")

# Teste F (robusto e clássico): regiões conjuntamente
regs = "norte = 0, nordeste = 0, sul = 0, centro_oeste = 0"
out["F_regioes_classico"] = float(m2.f_test(regs).fvalue)
out["F_regioes_hc1"] = float(m2.get_robustcov_results("HC1").f_test(regs).fvalue)
out["F_exper_classico"] = float(m2.f_test("exper = 0, exper2 = 0").fvalue)

# Viés de variável omitida: b_curto = b_longo + gamma * delta
ctrl = "superior + exper + exper2 + mulher + norte + nordeste + sul + centro_oeste + urbano"
delta = smf.ols(f"habilidade ~ educ + {ctrl}", data=df).fit().params["educ"]
out["ovb"] = {"b_curto": m3.params["educ"], "b_longo": m4.params["educ"],
              "gamma": m4.params["habilidade"], "delta": delta,
              "reconstrucao": m4.params["educ"] + m4.params["habilidade"] * delta}

# Heterocedasticidade (White) e VIF
w = het_white(m3.resid, m3.model.exog)
out["white_m3"] = {"LM": w[0], "p": w[1]}
X = m3.model.exog
out["vif_m3"] = {nome: variance_inflation_factor(X, i)
                 for i, nome in enumerate(m3.model.exog_names) if nome != "Intercept"}

# Efeito marginal da experiência e pico
b = m3.params
out["exper_marg_10"] = b["exper"] + 2 * b["exper2"] * 10
out["exper_marg_30"] = b["exper"] + 2 * b["exper2"] * 30
out["exper_pico"] = -b["exper"] / (2 * b["exper2"])

(BASE / "codigo" / "resultados_referencia.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

# =============================================================================
# Figuras
# =============================================================================
def virgula(v, _):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace("-", "−").replace(".", ",")


def salvar(fig, nome):
    for ax in fig.axes:  # decimais com vírgula (só eixos numéricos)
        for eixo in (ax.xaxis, ax.yaxis):
            if isinstance(eixo.get_major_formatter(), matplotlib.ticker.ScalarFormatter):
                eixo.set_major_formatter(matplotlib.ticker.FuncFormatter(virgula))
    fig.tight_layout()
    fig.savefig(IMG / nome, dpi=160)
    plt.close(fig)


# 1. Salário médio por nível de ensino (o "148%" da aula)
fig, ax = plt.subplots(figsize=(8, 4.6))
cores = [CINZA, CINZA, AZUL, LARANJA]
barras = ax.bar(ordem, desc["sal_hora"], color=cores, width=0.62, zorder=3)
for r, v in zip(barras, desc["sal_hora"]):
    ax.text(r.get_x() + r.get_width() / 2, v + 0.8, f"R$ {v:.2f}".replace(".", ","),
            ha="center", va="bottom", color=TINTA, fontsize=12)
ax.set_ylabel("Salário-hora médio (R$)")
ax.set_ylim(0, desc["sal_hora"].max() * 1.22)
ax.grid(axis="x", visible=False)
ax.annotate(f"+{out['premio_sup_medio_media']*100:.0f}%".replace(".", ","),
            xy=(3, desc.loc['Superior', 'sal_hora'] * 1.12), ha="center",
            color=LARANJA, fontsize=15, fontweight="bold")
ax.set_title("Superior × médio: salário-hora médio por nível de ensino", loc="left",
             fontsize=13, color=TINTA)
salvar(fig, "fig1_salario_por_nivel.png")

# 2. Simples em nível: salário-hora × educação
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
jit = np.random.default_rng(1).uniform(-0.25, 0.25, len(df))
xs = np.linspace(0, 20, 50)
axs[0].scatter(df["educ"] + jit, df["salario_hora"], s=8, alpha=0.25, color=AZUL, zorder=2, linewidths=0)
axs[0].plot(xs, s1.params["Intercept"] + s1.params["educ"] * xs, color=LARANJA, lw=2.2, zorder=3)
axs[0].set_ylim(0, 150)
axs[0].set_xlabel("Anos de estudo"); axs[0].set_ylabel("Salário-hora (R$)")
axs[0].set_title("Nível–nível", loc="left", fontsize=13)
axs[1].scatter(df["educ"] + jit, df["lsal"], s=8, alpha=0.25, color=AZUL, zorder=2, linewidths=0)
axs[1].plot(xs, s2.params["Intercept"] + s2.params["educ"] * xs, color=LARANJA, lw=2.2, zorder=3)
medias = df.groupby("educ")["lsal"].mean()
axs[1].plot(medias.index, medias.values, "o", ms=6, mfc="white", mec=TINTA, mew=1.4, zorder=4,
            label="média por ano de estudo")
axs[1].legend(frameon=False, loc="upper left", fontsize=10)
axs[1].set_xlabel("Anos de estudo"); axs[1].set_ylabel("ln(salário-hora)")
axs[1].set_title("Log–nível", loc="left", fontsize=13)
salvar(fig, "fig2_simples_nivel_log.png")

# 3. Caminho do coeficiente da educação (viés de variável omitida)
nomes = ["(S2) só educ", "(M1) + exper, sexo", "(M2) + região, urbano",
         "(M3) + superior", "(M4) + habilidade"]
mods = ["S2_log", "M1", "M2", "M3", "M4"]
coefs = [out[m]["coef"]["educ"] for m in mods]
eps = [out[m]["ep_hc1"]["educ"] for m in mods]
fig, ax = plt.subplots(figsize=(8.6, 4.4))
y = np.arange(len(nomes))[::-1]
ax.errorbar(coefs, y, xerr=1.96 * np.array(eps), fmt="o", color=AZUL, ms=8,
            ecolor=AZUL, elinewidth=2, capsize=0, zorder=3)
ax.axvline(0.075, color=LARANJA, lw=1.6, ls="--", zorder=2)
ax.text(0.075, len(nomes) - 0.35, " verdadeiro: 0,075", color=LARANJA, fontsize=11, va="bottom")
for c, yy in zip(coefs, y):
    ax.text(c, yy + 0.18, f"{c:.3f}".replace(".", ","), ha="center", fontsize=10.5, color=TINTA)
ax.set_yticks(y, nomes); ax.set_ylim(-0.6, len(nomes) - 0.1)
ax.set_xlabel("Coeficiente de educ (IC 95%, EP robusto)")
ax.grid(axis="y", visible=False)
ax.set_title("O retorno de um ano de estudo muda com os controles", loc="left", fontsize=13)
salvar(fig, "fig3_caminho_coeficiente.png")

# 4. Resíduos × ajustados (heterocedasticidade)
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.scatter(df["educ"] + jit, m3.resid, s=8, alpha=0.3, color=AZUL, linewidths=0, zorder=2)
dp = pd.Series(m3.resid).groupby(df["educ"]).std()
ax.plot(dp.index, 2 * dp.values, color=LARANJA, lw=2, zorder=3, label="±2 desvios-padrão por ano")
ax.plot(dp.index, -2 * dp.values, color=LARANJA, lw=2, zorder=3)
ax.axhline(0, color=TINTA, lw=1)
ax.legend(frameon=False, loc="lower left", fontsize=10)
ax.set_xlabel("Anos de estudo"); ax.set_ylabel("Resíduo do modelo M3")
ax.set_title("A dispersão dos resíduos cresce com a escolaridade", loc="left", fontsize=13)
salvar(fig, "fig4_residuos.png")

print(json.dumps({k: out[k] for k in ["premio_sup_medio_media", "ovb", "white_m3",
                                       "F_regioes_hc1", "exper_pico"]}, default=float, indent=1))
for m in ["S1_nivel", "S2_log", "S3_dummy", "S4_dummy_med_sup", "S5_nivel_dummy", "M1", "M2", "M3", "M4", "M5", "M6_niveis"]:
    o = out[m]
    print(f"\n{m}  n={o['n']}  R2={o['r2']:.3f}  R2a={o['r2a']:.3f}")
    for k in o["coef"]:
        print(f"  {k:14s} {o['coef'][k]: .4f}  ({o['ep_hc1'][k]:.4f})  [{o['ep_classico'][k]:.4f}]  p={o['p_hc1'][k]:.3f}")
