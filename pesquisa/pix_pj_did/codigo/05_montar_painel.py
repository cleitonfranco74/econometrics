"""
05 - Monta o painel município x mês (jan/2019 a dez/2024) para o artigo
"Efeito causal da chegada do Pix PJ ... (DiD escalonado)".

Junta as saídas de 01 (Pix), 02b (CNPJ), 03 (ESTBAN) e 04 (IBGE).
Universo: todos os municípios de MT, MS e GO (467). A amostra do artigo é
marcada por indicadoras (o pesquisador filtra na estimação):
  amostra_50a600mil : população 2019 entre 50 mil e 600 mil hab.
  amostra_artigo    : municípios listados em dados/amostra_artigo.csv
                      (coluna cod_ibge), se o arquivo existir — use para
                      informar os 33 municípios de Franco (2026).

TRATAMENTO (coorte G, em AAAAMM; 0 = nunca tratado até dez/2024)
  G_primeira_pj : 1º mês com ao menos uma transação Pix envolvendo PJ
                  (definição do artigo). Com dados MENSAIS do BCB, quase
                  todos os municípios caem em nov/2020 -> pouca variação.
  G_adesao10/25/50 : 1º mês em que a % de empresas ativas que RECEBEM Pix
                  (QT_PES_RecebedorPJ / empresas ativas) atinge 10/25/50%.
                  Alternativa com variação escalonada real (ver README).
  Para cada G_*, há D_* = 1[anomes >= G] e G_*_t (índice do período 1..72,
  formato exigido pelo pacote `did` do R).

RESULTADOS
  y1_pix_pj_por_empresa : transações Pix com PJ / empresas ativas
                          (0 antes de nov/2020: o Pix não existia)
  y2_aberturas_mei      : novos MEIs no mês
  y3_ihh_credito        : IHH do crédito (ESTBAN 160) entre instituições
  y4_idf                : NÃO incluído (IDF-MT de Franco, 2026, é externo;
                          junte pela chave cod_ibge + ano)
  y5_credito_pc         : crédito total ESTBAN / população (R$)
  + versões asinh() de y1, y2 e y5.

COVARIÁVEIS PRÉ-TRATAMENTO (fixas no tempo)
  ln_pop_2019, idhm_2010, ln_pib_pc_2019, campus (estab. ativo com CNAE de
  educação superior em dez/2019), pct_simples_2019, uf

Saídas: dados/painel_pix_pj_mensal.csv  e  dados/painel_pix_pj_anual.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
SAIDA = RAIZ / "dados"

meses = pd.period_range("2019-01", "2024-12", freq="M")
anomes = [m.year * 100 + m.month for m in meses]
periodo = {a: i + 1 for i, a in enumerate(anomes)}  # 201901 -> 1 ... 202412 -> 72

pix = pd.read_csv(PROC / "pix_municipio_mes.csv")
# CNPJ (Receita) é opcional: só entra se o script 02b tiver sido rodado
TEM_CNPJ = (PROC / "cnpj_municipio_mes.csv").exists()
if TEM_CNPJ:
    cnpj = pd.read_csv(PROC / "cnpj_municipio_mes.csv")
    cnpj19 = pd.read_csv(PROC / "cnpj_municipio_2019.csv")
estban = pd.read_csv(PROC / "estban_municipio_mes.csv")
cov = pd.read_csv(PROC / "covariaveis_municipio_ano.csv")

muns = pix[["cod_ibge", "Municipio", "UF"]].drop_duplicates("cod_ibge")
muns = muns.rename(columns={"Municipio": "municipio", "UF": "uf"})
grade = muns.merge(pd.DataFrame({"anomes": anomes}), how="cross")
grade["ano"] = grade.anomes // 100
grade["mes"] = grade.anomes % 100
grade["periodo"] = grade.anomes.map(periodo)

# --- Pix ---------------------------------------------------------------
pcols = ["qt_pix_pj", "vl_pix_pj", "qt_pix_total", "QT_PagadorPJ",
         "QT_RecebedorPJ", "VL_RecebedorPJ", "QT_PES_RecebedorPJ",
         "QT_PES_PagadorPJ"]
p = pix[["cod_ibge", "anomes"] + pcols].rename(columns=str.lower)
painel = grade.merge(p, on=["cod_ibge", "anomes"], how="left")
antes_pix = painel.anomes < 202011
pc = [c.lower() for c in pcols]
painel.loc[antes_pix, pc] = painel.loc[antes_pix, pc].fillna(0)

# --- CNPJ --------------------------------------------------------------
if TEM_CNPJ:
    painel = painel.merge(cnpj, on=["cod_ibge", "anomes"], how="left")

# --- ESTBAN (pelo código IBGE; casos sem agência ficam vazios) --------------
e = estban.drop(columns=["uf", "codmun", "municipio"]).rename(
    columns={"codmun_ibge": "cod_ibge"})
painel = painel.merge(e, on=["cod_ibge", "anomes"], how="left")
painel["tem_agencia_estban"] = painel["credito_total"].notna().astype(int)

# --- Covariáveis anuais e pré-tratamento ----------------------------------
painel = painel.merge(cov[["cod_ibge", "ano", "pop", "pib_pc"]],
                      on=["cod_ibge", "ano"], how="left")
c19 = cov[cov.ano == 2019].set_index("cod_ibge")
fixas = pd.DataFrame({
    "pop_2019": c19["pop"],
    "ln_pop_2019": np.log(c19["pop"]),
    "ln_pib_pc_2019": np.log(c19["pib_pc"]),
    "idhm_2010": c19["idhm_2010"],
}).reset_index()
if TEM_CNPJ:
    fixas = fixas.merge(cnpj19, on="cod_ibge", how="left")
painel = painel.merge(fixas, on="cod_ibge", how="left")

# --- Resultados ------------------------------------------------------------
# Y1 sem o CNPJ: transações Pix com PJ por mil habitantes (e por empresa
# recebedora de Pix). Com o CNPJ: por empresa ativa, como no artigo.
painel["y1_pix_pj_mil_hab"] = 1000 * painel.qt_pix_pj / painel["pop"]
painel["y1b_pix_pj_por_recebedora"] = (painel.qt_recebedorpj
                                       / painel.qt_pes_recebedorpj.replace(0, np.nan))
painel["empresas_recebem_pix_mil_hab"] = 1000 * painel.qt_pes_recebedorpj / painel["pop"]
painel["y3_ihh_credito"] = painel.ihh_credito
painel["y5_credito_pc"] = painel.credito_total / painel["pop"]
ys = ["y1_pix_pj_mil_hab", "y5_credito_pc"]
if TEM_CNPJ:
    painel["y1_pix_pj_por_empresa"] = painel.qt_pix_pj / painel.ativas
    painel["y2_aberturas_mei"] = painel.aberturas_mei
    painel["pct_empresas_recebem_pix"] = 100 * painel.qt_pes_recebedorpj / painel.ativas
    ys += ["y1_pix_pj_por_empresa", "y2_aberturas_mei"]
for c in ys:
    painel["asinh_" + c] = np.arcsinh(painel[c])

# --- Tratamento ------------------------------------------------------------
def coorte(mask):
    g = painel[mask].groupby("cod_ibge").anomes.min()
    return painel.cod_ibge.map(g).fillna(0).astype(int)

defs = {"G_primeira_pj": painel.qt_pix_pj > 0}
# Difusão: mês em que o nº de empresas que recebem Pix no município atinge
# 25% / 50% do seu próprio nível médio de 2024 (medida sem escala, não
# depende do nº de empresas ativas).
ref24 = painel[painel.ano == 2024].groupby("cod_ibge").qt_pes_recebedorpj.mean()
frac = painel.qt_pes_recebedorpj / painel.cod_ibge.map(ref24)
for lim in (25, 50):
    defs[f"G_difusao{lim}"] = frac >= lim / 100
if TEM_CNPJ:
    for lim in (10, 25, 50):
        defs[f"G_adesao{lim}"] = painel.pct_empresas_recebem_pix >= lim
for nome, mask in defs.items():
    painel[nome] = coorte(mask)
    painel[nome + "_t"] = painel[nome].map(periodo).fillna(0).astype(int)
    painel["D" + nome[1:]] = ((painel[nome] > 0)
                              & (painel.anomes >= painel[nome])).astype(int)

# --- Amostras --------------------------------------------------------------
painel["amostra_50a600mil"] = painel.pop_2019.between(50_000, 600_000).astype(int)
lista = SAIDA / "amostra_artigo.csv"
if lista.exists():
    ids = set(pd.read_csv(lista).cod_ibge)
    painel["amostra_artigo"] = painel.cod_ibge.isin(ids).astype(int)

painel["id"] = painel.cod_ibge  # identificador numérico para o `did`
painel = painel.sort_values(["cod_ibge", "anomes"])
painel.to_csv(SAIDA / "painel_pix_pj_mensal.csv", index=False)
painel[painel.amostra_50a600mil == 1].to_csv(
    SAIDA / "painel_pix_pj_mensal_amostra40.csv", index=False)

# --- Painel anual (para a robustez com IDF-MT anual) -----------------------
soma = ["qt_pix_pj", "vl_pix_pj"]
dez = ["credito_total", "ihh_credito", "n_agencias", "n_instituicoes",
       "pop", "pib_pc"]
if TEM_CNPJ:
    soma += ["aberturas_cnpj", "aberturas_mei", "opcoes_mei", "baixas_cnpj"]
    dez += ["ativas", "ativas_mei", "ativas_simples"]
fix = [c for c in painel.columns if c.endswith("_2019") or c.endswith("_2010")
       or c.startswith("G_") or c.startswith("amostra") or c == "campus"]
anual = (painel.groupby(["cod_ibge", "municipio", "uf", "ano"])[soma].sum(min_count=1)
         .join(painel[painel.mes == 12].set_index(["cod_ibge", "municipio", "uf", "ano"])[dez])
         .join(painel.groupby(["cod_ibge", "municipio", "uf", "ano"])[fix].first())
         .reset_index())
if TEM_CNPJ:  # CNPJ termina em set/2024: soma anual de 2024 seria parcial
    cnpj_anual = [c for c in soma + dez if c in cnpj.columns]
    anual.loc[anual.ano == 2024, cnpj_anual] = np.nan
anual["y1_pix_pj_mil_hab"] = 1000 * anual.qt_pix_pj / anual["pop"]
if TEM_CNPJ:
    anual["y1_pix_pj_por_empresa"] = anual.qt_pix_pj / anual.ativas
anual["y5_credito_pc"] = anual.credito_total / anual["pop"]
anual.to_csv(SAIDA / "painel_pix_pj_anual.csv", index=False)

# --- Coortes da amostra ---------------------------------------------------
gcols = [c for c in painel.columns if c.startswith("G_") and not c.endswith("_t")]
uma40 = painel[painel.amostra_50a600mil == 1].drop_duplicates("cod_ibge")
coortes = pd.concat({g: uma40[g].value_counts() for g in gcols}, axis=1)
coortes.index.name = "coorte_anomes"
coortes.fillna(0).astype(int).sort_index().to_csv(SAIDA / "coortes_amostra40.csv")
uma40[["cod_ibge", "municipio", "uf", "pop_2019"] + gcols].sort_values(
    "pop_2019", ascending=False).to_csv(SAIDA / "municipios_amostra40.csv", index=False)

# --- Resumo ----------------------------------------------------------------
print("Painel mensal:", painel.shape, "| anual:", anual.shape)
uma = painel.drop_duplicates("cod_ibge")
for nome in defs:
    print(f"\nCoortes {nome} (todos / amostra 50-600 mil):")
    t = pd.concat([uma[nome].value_counts(), uma.loc[uma.amostra_50a600mil == 1, nome]
                   .value_counts()], axis=1, keys=["todos", "amostra"]).fillna(0)
    print(t.sort_index().astype(int).to_string())
