"""
01 - Mural de Licitações do TCE-PR (dados abertos): todos os processos de
contratação dos 399 municípios do Paraná (prefeituras, câmaras, autarquias).

Fonte: https://servicos.tce.pr.gov.br/servicos/arquivos/dadosabertos/MuralDeLicitacoes/
       (um CSV por ano de carga; dicionário de dados na mesma pasta)

COBERTURA EFETIVA (pela data de abertura do processo):
   2018T1-2021T1 completos | 2021T2 parcial (arquivo encerrado em 13/04/2021)
   2021T3-2024T4 praticamente ausentes (não há arquivos de 2022 e 2023 e o de
   2024 só tem o 1º trimestre) | 2025T1-2026T1 completos | 2026T2 parcial.
O painel usa apenas os trimestres completos: 2018T1-2021T1 e 2025T1-2026T1.

LIMITAÇÃO: o Mural NÃO distingue pregão eletrônico de presencial e não traz
nº de licitantes, preço homologado nem fornecedor. A adoção da forma
eletrônica é medida no PNCP (script 02).

Saídas (dados/processados/):
  mural_processos.csv            - processos deduplicados (2018-2026)
  mural_municipio_trimestre.csv  - painel município x trimestre (trimestres completos)
  mural_cobertura_trimestral.csv - nº de processos por trimestre (diagnóstico)
"""
import io
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "tcepr"
PROC = RAIZ / "dados" / "processados"
PROC.mkdir(parents=True, exist_ok=True)
BASE = ("https://servicos.tce.pr.gov.br/servicos/arquivos/dadosabertos/"
        "MuralDeLicitacoes/{a}_mural_de_licitacoes_base_de_dados.csv")
ANOS = [2018, 2019, 2020, 2021, 2024, 2025, 2026]
TRIM_OK = ([pd.Period(f"{a}Q{q}") for a in (2018, 2019, 2020) for q in (1, 2, 3, 4)]
           + [pd.Period("2021Q1")]
           + [pd.Period(f"2025Q{q}") for q in (1, 2, 3, 4)] + [pd.Period("2026Q1")])


def ler(ano):
    arq = BRUTOS / f"{ano}_mural.csv"
    if not arq.exists():
        import urllib.request
        BRUTOS.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(BASE.format(a=ano), arq)
    raw = arq.read_bytes()
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:          # arquivos até 2021 vêm em latin-1
        txt = raw.decode("latin1")
    linhas = txt.splitlines()
    # 2ª linha do arquivo é uma régua de "-----"; descartamos
    d = pd.read_csv(io.StringIO("\n".join([linhas[0]] + linhas[2:])), sep=";",
                    dtype=str, on_bad_lines="skip")
    d["arquivo"] = ano
    return d


d = pd.concat([ler(a) for a in ANOS], ignore_index=True)
d = d[d["cdIBGE"].str.strip().str.fullmatch(r"\d{1,5}", na=False)].copy()  # descarta linhas quebradas
d["cod_ibge"] = ("41" + d["cdIBGE"].str.strip().str.zfill(5)).astype(int)
d["data"] = pd.to_datetime(d["dtAberturaLicitacao"].str[:10], dayfirst=True, errors="coerce")
pub = pd.to_datetime(d["dtLancamentoPublicacao"].str[:10], dayfirst=True, errors="coerce")
d["data"] = d["data"].where(d["data"].between("2017-01-01", "2026-12-31"), pub)
d["cancelado"] = d["dtCancelamento"].notna() & d["dtCancelamento"].str.strip().ne("")
d["valor_ref"] = pd.to_numeric(d["vlReferencia"].str.replace(",", ".", regex=False),
                               errors="coerce")
# mesmo processo pode aparecer em mais de um arquivo anual: fica a última carga
chave = ["cod_ibge", "nrDocumento", "nrAno", "nrProcessoEdital", "dsModalidadeLicitacao"]
d = d.sort_values("arquivo").drop_duplicates(chave, keep="last")

m = d["dsModalidadeLicitacao"].fillna("")
d["tipo"] = np.select(
    [m.str.contains("Preg"), m.str.contains("Concorr"), m.str.contains("Tomada"),
     m.str.contains("Convite"), m.str.contains("Dispensa"), m.str.contains("Inexig"),
     m.str.contains("Diferenciado")],
    ["pregao", "concorrencia", "tomada", "convite", "dispensa", "inexigibilidade", "rdc"],
    default="outros")
d["competitivo"] = d["tipo"].isin(["pregao", "concorrencia", "tomada", "convite", "rdc"])
d["direta"] = d["tipo"].isin(["dispensa", "inexigibilidade"])
obj = d["dsObjeto"].fillna("")
d["cita_eletronico"] = obj.str.contains("eletr[ôo]nic", case=False, regex=True)
d["cita_presencial"] = obj.str.contains("presencial", case=False)
d["trimestre"] = d["data"].dt.to_period("Q")

cols = ["cod_ibge", "nmMunicipio", "nrDocumento", "nmRazaoSocial", "nrAno",
        "nrProcessoEdital", "dsModalidadeLicitacao", "tipo", "competitivo", "direta",
        "dsTipoAvaliacao", "data", "trimestre", "valor_ref", "cancelado",
        "cita_eletronico", "cita_presencial", "flExclusivoEPPME", "arquivo", "dsObjeto"]
d[cols].to_csv(PROC / "mural_processos.csv", index=False)

cob = (d[d.data.between("2018-01-01", "2026-12-31")].groupby("trimestre").size()
       .rename("processos").reset_index())
cob["trimestre_completo"] = cob.trimestre.isin(TRIM_OK).astype(int)
cob.to_csv(PROC / "mural_cobertura_trimestral.csv", index=False)

# ---- painel município x trimestre (somente processos não cancelados) -------
v = d[~d.cancelado & d.trimestre.isin(TRIM_OK)].copy()
v["vr"] = v["valor_ref"].clip(lower=0)
g = v.groupby(["cod_ibge", "trimestre"])
pan = pd.DataFrame({
    "n_processos": g.size(),
    "n_competitivos": g["competitivo"].sum(),
    "n_pregoes": g.apply(lambda x: (x.tipo == "pregao").sum()),
    "n_concorrencias": g.apply(lambda x: (x.tipo == "concorrencia").sum()),
    "n_tomada_convite": g.apply(lambda x: x.tipo.isin(["tomada", "convite"]).sum()),
    "n_dispensas": g.apply(lambda x: (x.tipo == "dispensa").sum()),
    "n_inexigibilidades": g.apply(lambda x: (x.tipo == "inexigibilidade").sum()),
    "n_diretas": g["direta"].sum(),
    "n_exclusivo_me_epp": g["flExclusivoEPPME"].apply(lambda s: s.eq("1").sum()),
    "vr_total": g["vr"].sum(),
    "vr_diretas": g.apply(lambda x: x.loc[x.direta, "vr"].sum()),
    "vr_competitivos": g.apply(lambda x: x.loc[x.competitivo, "vr"].sum()),
})
# grade completa: município sem processo no trimestre = 0
grade = pd.MultiIndex.from_product([sorted(d.cod_ibge.unique()), TRIM_OK],
                                   names=["cod_ibge", "trimestre"])
pan = pan.reindex(grade, fill_value=0).reset_index()
pan["ano"] = pan.trimestre.dt.year
pan["tri"] = pan.trimestre.dt.quarter
pan["share_diretas"] = pan.n_diretas / pan.n_processos.replace(0, np.nan)
pan["share_diretas_valor"] = pan.vr_diretas / pan.vr_total.replace(0, np.nan)
pan["trimestre"] = pan.trimestre.astype(str)
pan.to_csv(PROC / "mural_municipio_trimestre.csv", index=False)
print(pan.shape, "| municípios:", pan.cod_ibge.nunique())
print(pan.groupby("ano")[["n_processos", "n_pregoes", "n_diretas"]].sum())
