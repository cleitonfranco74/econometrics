"""
04 - Monta os painéis para as estimações do art. 176 (Paraná).

Entradas: saídas de 01 (Mural TCE-PR), 02 (PNCP) e 03 (covariáveis).

ADOÇÃO DA FORMA ELETRÔNICA (eq. 1 do projeto, adaptada)
  O Mural não distingue eletrônico de presencial e não cobre 2022-2024.
  Por isso:
     Elet(i,t) = nº de certames ELETRÔNICOS (pregão + concorrência) do
                 município publicados no PNCP no ano t
                 / média anual de certames competitivos do município no
                 Mural em 2018-2020
  (o denominador é o volume "normal" de licitações do município e existe
   para todos). Limitada a 1. Disponível para 2021-2026.
  G_elet50 = 1º ano com Elet >= 0,5 (robustez: 0,25 e 0,75); 0 = nunca.
  Atenção: antes de 2024 a publicação no PNCP era facultativa para quem
  licitava pela Lei 8.666/10.520; Elet subestima o pregão eletrônico
  realizado em outras plataformas nesse período.

TRATAMENTO LEGAL (art. 176)
  obrigado = 1[população do Censo 2022 > 20.000]  (robustez: estimativa 2021)
  pos      = 1[período >= 2024]

Saídas (dados/):
  painel_trimestral.csv   município x trimestre (trimestres completos do Mural)
  painel_anual.csv        município x ano 2018-2026 (desfechos só em anos completos)
  primeiro_estagio_faixas.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
SAIDA = RAIZ / "dados"
CORTE = 20_000

mur = pd.read_csv(PROC / "mural_municipio_trimestre.csv")
cov = pd.read_csv(PROC / "covariaveis_pr.csv")
pn = pd.read_csv(PROC / "pncp_compras_pr.csv", low_memory=False)
pn = pn[pn.cod_ibge.notna()].copy()
pn["cod_ibge"] = pn.cod_ibge.astype(int)
pn["ano"] = pd.to_datetime(pn.data_publicacao).dt.year
pn["eletronico"] = pn.modalidade_id.isin([4, 6])

# ---- Adoção pelo PNCP --------------------------------------------------------
base = mur[mur.ano <= 2020].groupby("cod_ibge").n_competitivos.sum() / 3
anos = range(2021, 2027)
el = (pn[pn.eletronico].groupby(["cod_ibge", "ano"]).size()
      .unstack(fill_value=0).reindex(index=cov.cod_ibge, columns=anos, fill_value=0))
pr = (pn[~pn.eletronico].groupby(["cod_ibge", "ano"]).size()
      .unstack(fill_value=0).reindex(index=cov.cod_ibge, columns=anos, fill_value=0))
elet = el.div(base.reindex(el.index).replace(0, np.nan), axis=0).clip(upper=1)
adoc = pd.DataFrame(index=cov.cod_ibge)
for lim in (25, 50, 75):
    ok = elet >= lim / 100
    adoc[f"G_elet{lim}"] = ok.idxmax(axis=1).where(ok.any(axis=1), 0).astype(int)
adoc["media_competitivos_2018_20"] = base.reindex(adoc.index)

# ---- Covariáveis e grupos -----------------------------------------------------
c = cov.set_index("cod_ibge")
c["obrigado"] = (c.pop_2022_censo > CORTE).astype(int)
c["obrigado_pop2021"] = (c.pop_2021 > CORTE).astype(int)
c["pop_centrada"] = c.pop_2022_censo - CORTE
c["ln_pop_2019"] = np.log(c.pop_2019)
c["ln_pib_pc_2019"] = np.log(c.pib_pc_2019)
c["ln_rec_propria_pc_2019"] = np.log(c.rec_propria_pc_2019)
med = c.rec_propria_pc_2019.median()
c["baixa_capacidade"] = (c.rec_propria_pc_2019 < med).astype(int)
# entorno de Curitiba (capital + municípios a até 60 km em linha reta),
# para a robustez (b) do projeto, que exclui Curitiba e a região metropolitana
c["entorno_curitiba"] = (c.dist_curitiba_km <= 60).astype(int)
# janela do desenho de descontinuidade (bandwidth do projeto: 2.900 hab.)
c["janela_2900"] = c.pop_centrada.abs().le(2900).astype(int)
c["janela_3000"] = c.pop_centrada.abs().le(3000).astype(int)
# placebo interno (H5): já eletrônico em 2023, antes da obrigação
c["ja_eletronico_2023"] = (elet[2023] >= 0.5).reindex(c.index).fillna(False).astype(int)
c = c.join(adoc)

# ---- Painel trimestral ----------------------------------------------------------
t = mur.merge(c.reset_index(), on="cod_ibge", how="left")
t["pos"] = (t.ano >= 2024).astype(int)
t["obrig_pos"] = t.obrigado * t.pos
ordem = {q: i + 1 for i, q in enumerate(sorted(t.trimestre.unique()))}
t["periodo"] = t.trimestre.map(ordem)
t["asinh_n_processos"] = np.arcsinh(t.n_processos)
t["asinh_n_competitivos"] = np.arcsinh(t.n_competitivos)
t["asinh_n_diretas"] = np.arcsinh(t.n_diretas)
t.to_csv(SAIDA / "painel_trimestral.csv", index=False)

# ---- Painel anual -----------------------------------------------------------------
ANOS_OK = [2018, 2019, 2020, 2025]          # anos com os 4 trimestres no Mural
soma = ["n_processos", "n_competitivos", "n_pregoes", "n_concorrencias",
        "n_tomada_convite", "n_dispensas", "n_inexigibilidades", "n_diretas",
        "vr_total", "vr_diretas", "vr_competitivos"]
a = mur[mur.ano.isin(ANOS_OK)].groupby(["cod_ibge", "ano"])[soma].sum().reset_index()
grade = pd.MultiIndex.from_product([c.index, range(2018, 2027)],
                                   names=["cod_ibge", "ano"]).to_frame(index=False)
a = grade.merge(a, how="left")
a["share_diretas"] = a.n_diretas / a.n_processos.replace(0, np.nan)
a["share_diretas_valor"] = a.vr_diretas / a.vr_total.replace(0, np.nan)
el_l = el.stack().rename("pncp_eletronicos").reset_index()
pr_l = pr.stack().rename("pncp_presenciais").reset_index()
ee = elet.stack().rename("elet").reset_index()
a = a.merge(el_l, how="left").merge(pr_l, how="left").merge(ee, how="left")
a = a.merge(c.reset_index(), on="cod_ibge", how="left")
a["pos"] = (a.ano >= 2024).astype(int)
a["obrig_pos"] = a.obrigado * a.pos
for lim in (25, 50, 75):
    g = a[f"G_elet{lim}"]
    a[f"D_elet{lim}"] = ((g > 0) & (a.ano >= g)).astype(int)
a.to_csv(SAIDA / "painel_anual.csv", index=False)

# ---- Primeiro estágio por faixa -----------------------------------------------------
faixa = pd.cut(c.pop_2022_censo, [0, 5e3, 10e3, 15e3, 20e3, 25e3, 50e3, 1e9],
               labels=["<5 mil", "5-10 mil", "10-15 mil", "15-20 mil", "20-25 mil",
                       "25-50 mil", ">50 mil"])
fe = (elet.ge(0.5).groupby(faixa, observed=True).mean()
      .add_prefix("pct_elet50_").round(3))
fe["n_municipios"] = faixa.value_counts().reindex(fe.index)
fe.to_csv(SAIDA / "primeiro_estagio_faixas.csv")
print("trimestral:", t.shape, "| anual:", a.shape)
print("coortes G_elet50:", c.G_elet50.value_counts().sort_index().to_dict())
print("obrigados:", c.obrigado.sum(), "| janela 2.900:", c.janela_2900.sum(),
      "(", c[c.janela_2900 == 1].obrigado.sum(), "acima )")
