"""
04 - Painel município x mês, jan/2023 a dez/2025, para o artigo das bets.

  Desfechos (per capita, R$): poupança (ESTBAN 420), depósitos à vista
  (401-419), depósitos a prazo (432), operações de crédito (160; PF+PJ: o
  ESTBAN não separa) e ISS (SICONFI, RREO Anexo 3).
  Exposição (fixa no tempo): DigYouth (Censo 2022 x Anatel 2022), em
  desvios-padrão (digyouth_z), quartis e decis.

  Tempo: post = t >= out/2024 (bloqueio da Anatel); block = out-dez/2024;
  legal = t >= jan/2025 (vigência plena da Lei 14.790/2023);
  rel = meses relativos a out/2024 (k = -1 é set/2024).

  Amostra ESTBAN: municípios com agência em todos os 36 meses (painel
  balanceado, como no Quadro 1 do artigo).

Saída: dados/painel_bets_mensal.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"

est = pd.read_csv(PROC / "estban_municipio_mes.csv")
est = est.rename(columns={"codmun_ibge": "cod_ibge"})
est = est[est.cod_ibge.notna()].copy()
est["cod_ibge"] = est.cod_ibge.astype(int)
est = est.groupby(["cod_ibge", "anomes"], as_index=False).agg(
    poupanca=("dep_poupanca", "sum"), dep_vista=("dep_vista", "sum"),
    dep_prazo=("dep_prazo", "sum"), credito=("credito_total", "sum"),
    n_agencias=("n_agencias", "sum"), estban_imputado=("estban_imputado", "max"))
meses = sorted(est.anomes.unique())
completos = est.groupby("cod_ibge").anomes.nunique()
est["balanceado"] = est.cod_ibge.map(completos.eq(len(meses))).astype(int)

arq_iss = PROC / "iss_municipio_mes.csv"   # opcional (script 02)
iss = (pd.read_csv(arq_iss) if arq_iss.exists()
       else pd.DataFrame(columns=["cod_ibge", "anomes", "iss"]).astype(float))
cov = pd.read_csv(PROC / "covariaveis_municipio.csv")
pop = pd.read_csv(PROC / "populacao_municipio_ano.csv")

grade = cov[["cod_ibge"]].merge(pd.DataFrame({"anomes": meses}), how="cross")
p = (grade.merge(est, how="left").merge(iss, how="left").merge(cov, how="left"))
p["ano"] = p.anomes // 100
p["mes"] = p.anomes % 100
p = p.merge(pop, on=["cod_ibge", "ano"], how="left")
p["tem_estban"] = p.poupanca.notna().astype(int)

for v in ["poupanca", "dep_vista", "dep_prazo", "credito", "iss"]:
    p[v + "_pc"] = p[v] / p["pop"]
    p["ln_" + v + "_pc"] = np.log(p[v + "_pc"].where(p[v + "_pc"] > 0))
p["asinh_iss_pc"] = np.arcsinh(p.iss_pc)
p["ln_agencias"] = np.log1p(p.n_agencias)

t = (p.ano - 2024) * 12 + (p.mes - 10)          # out/2024 = 0
p["rel"] = t
p["periodo"] = (p.ano - 2023) * 12 + p.mes       # jan/2023 = 1
p["post"] = (t >= 0).astype(int)
p["block"] = ((t >= 0) & (t <= 2)).astype(int)
p["legal"] = (t >= 3).astype(int)

d = cov.set_index("cod_ibge").digyouth
p["digyouth_z"] = p.cod_ibge.map((d - d.mean()) / d.std())
p["digyouth_q"] = p.cod_ibge.map(pd.qcut(d, 4, labels=False) + 1)
p["digyouth_dec"] = p.cod_ibge.map(pd.qcut(d, 10, labels=False) + 1)
# medida demográfica pura (sem banda larga) e banda larga pura, para robustez
for v in ["sh_homens_18_35", "banda_larga_100dom"]:
    p[v + "_z"] = (p[v] - cov[v].mean()) / cov[v].std()
med_pib = cov.pib_pc_2021.median()
med_jov = cov.sh_jovens_18_35.median()
p["baixa_renda"] = (p.pib_pc_2021 < med_pib).astype(int)
p["mais_jovens"] = (p.sh_jovens_18_35 > med_jov).astype(int)
p["pop_20k_500k"] = p.pop_2022.between(20_000, 500_000).astype(int)
p.to_csv(RAIZ / "dados" / "painel_bets_mensal.csv", index=False)
b = p[(p.balanceado == 1)]
print(p.shape, "| municípios com ESTBAN balanceado:", b.cod_ibge.nunique(),
      "| com ISS:", p[p.iss.notna()].cod_ibge.nunique())
print("correlação DigYouth x ln PIB pc:",
      round(np.corrcoef(cov.digyouth, np.log(cov.pib_pc_2021))[0, 1], 2))
