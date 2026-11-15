"""
02b - Processa o Cadastro CNPJ (Receita Federal) para MT, MS e GO e monta
séries mensais de empresas por município (jan/2019 a dez/2024).

Entrada: zips baixados por 02a_baixar_cnpj.sh em dados/brutos/cnpj/
Layout:  "LAYOUT_DADOS_ABERTOS_CNPJ.pdf" da Receita (arquivos sem cabeçalho,
         separador ";", codificação latin-1, datas AAAAMMDD).

Como o cadastro é uma "foto" (snapshot) da data de referência, a história
mensal é RECONSTRUÍDA a partir das datas de cada estabelecimento:
  - abertura  : data_inicio_atividade
  - baixa     : data_situacao_cadastral quando situação = 08 (baixada)
  - ativo em t: aberto até t e (hoje ativo OU mudou de situação depois de t)
  - MEI       : data_opcao_mei / data_exclusao_mei (arquivo Simples)
Limitação: o arquivo guarda só a ÚLTIMA situação e a ÚLTIMA opção pelo
Simples/MEI de cada empresa; idas e vindas anteriores se perdem. É a mesma
base usada pelo Mapa de Empresas (MEMP), que também é construída a partir
do CNPJ da Receita.

Saídas (dados/processados/):
  cnpj_municipio_mes.csv   - séries mensais por município (código IBGE)
  cnpj_municipio_2019.csv  - covariáveis pré-tratamento (dez/2019)
  correspondencia_municipios_rf_ibge.csv

Execute de dentro de codigo/:  python 02b_processar_cnpj.py
"""
import io
import re
import subprocess
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CNPJ = RAIZ / "dados" / "brutos" / "cnpj"
PROC = RAIZ / "dados" / "processados"
UFS = ("MT", "MS", "GO")
MESES = pd.period_range("2019-01", "2024-12", freq="M")
CNAE_SUPERIOR = {"8531700", "8532500"}  # educação superior (graduação; grad.+pós)

# ----------------------------------------------------------------------------
# 1. Estabelecimentos (filtra as linhas das três UFs já no fluxo do unzip)
# ----------------------------------------------------------------------------
COLS_EST = {0: "cnpj_basico", 1: "cnpj_ordem", 2: "cnpj_dv", 3: "matriz",
            5: "situacao", 6: "data_situacao", 10: "data_inicio",
            11: "cnae", 19: "uf", 20: "mun_rf"}
padrao = r';"(MT|MS|GO)";"[0-9]{4}";'
partes = []
for i in range(10):
    arq = CNPJ / f"Estabelecimentos{i}.zip"
    # unzip -p | grep: muito mais rápido que ler 25 GB inteiros no pandas
    p1 = subprocess.Popen(["unzip", "-p", str(arq)], stdout=subprocess.PIPE)
    p2 = subprocess.run(["grep", "-aE", padrao], stdin=p1.stdout,
                        capture_output=True)
    p1.wait()
    df = pd.read_csv(io.BytesIO(p2.stdout), sep=";", header=None, dtype=str,
                     encoding="latin1", usecols=list(COLS_EST),
                     quotechar='"', on_bad_lines="warn")
    df = df.rename(columns=COLS_EST)
    df = df[df.uf.isin(UFS)]
    partes.append(df)
    print(f"Estabelecimentos{i}: {len(df):,} linhas de MT/MS/GO")
est = pd.concat(partes, ignore_index=True)
del partes

for c in ("data_inicio", "data_situacao"):
    est[c] = pd.to_datetime(est[c], format="%Y%m%d", errors="coerce")
est["situacao"] = est["situacao"].astype(int)
est["matriz"] = est["matriz"].astype(int).eq(1)

# ----------------------------------------------------------------------------
# 2. Simples/MEI e Empresas (porte, natureza jurídica) — só CNPJs do recorte
# ----------------------------------------------------------------------------
basicos = set(est.cnpj_basico)


def ler_filtrado(zips, colunas):
    out = []
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            with zf.open(zf.namelist()[0]) as f:
                for bloco in pd.read_csv(f, sep=";", header=None, dtype=str,
                                         encoding="latin1", chunksize=2_000_000,
                                         usecols=list(colunas)):
                    out.append(bloco[bloco[0].isin(basicos)])
    return pd.concat(out).rename(columns=colunas)


simples = ler_filtrado([CNPJ / "Simples.zip"],
                       {0: "cnpj_basico", 1: "opcao_simples", 2: "data_opcao_simples",
                        3: "data_exclusao_simples", 4: "opcao_mei",
                        5: "data_opcao_mei", 6: "data_exclusao_mei"})
for c in [c for c in simples.columns if c.startswith("data_")]:
    simples[c] = pd.to_datetime(simples[c], format="%Y%m%d", errors="coerce")
empresas = ler_filtrado([CNPJ / f"Empresas{i}.zip" for i in range(10)],
                        {0: "cnpj_basico", 2: "natureza", 5: "porte"})
est = (est.merge(simples, on="cnpj_basico", how="left")
          .merge(empresas.drop_duplicates("cnpj_basico"), on="cnpj_basico", how="left"))
print("Simples:", len(simples), "| Empresas:", len(empresas))

# ----------------------------------------------------------------------------
# 3. Correspondência código Receita (TOM) -> código IBGE, por nome + UF
# ----------------------------------------------------------------------------
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", s.upper())


with zipfile.ZipFile(CNPJ / "Municipios.zip") as zf:
    mrf = pd.read_csv(zf.open(zf.namelist()[0]), sep=";", header=None,
                      dtype=str, encoding="latin1", names=["mun_rf", "nome_rf"])
pix = pd.read_csv(PROC / "pix_municipio_mes.csv",
                  usecols=["cod_ibge", "Municipio", "UF"]).drop_duplicates("cod_ibge")
pix["chave"] = pix.UF + "|" + pix.Municipio.map(norm)
usados = est[["mun_rf", "uf"]].drop_duplicates().merge(mrf, how="left")
usados["chave"] = usados.uf + "|" + usados.nome_rf.map(norm)
# grafias divergentes conhecidas entre Receita e IBGE
APELIDOS = {}  # preenchido após conferir a lista de não encontrados
usados["chave"] = usados["chave"].replace(APELIDOS)
corr = usados.merge(pix[["chave", "cod_ibge"]], on="chave", how="left")
corr.to_csv(PROC / "correspondencia_municipios_rf_ibge.csv", index=False)
sem = corr[corr.cod_ibge.isna()]
print("Municípios sem correspondência IBGE:", len(sem), sem.nome_rf.tolist())
est = est.merge(corr[["mun_rf", "uf", "cod_ibge"]], on=["mun_rf", "uf"], how="left")
est = est[est.cod_ibge.notna()].copy()
est["cod_ibge"] = est["cod_ibge"].astype(int)

# ----------------------------------------------------------------------------
# 4. Séries mensais por município
# ----------------------------------------------------------------------------
ini_m = est.data_inicio.dt.to_period("M")
sit_m = est.data_situacao.dt.to_period("M")
mei_ini = est.data_opcao_mei.dt.to_period("M")
mei_fim = est.data_exclusao_mei.dt.to_period("M")
sn_ini = est.data_opcao_simples.dt.to_period("M")
sn_fim = est.data_exclusao_simples.dt.to_period("M")
eh_mei_hoje_ou_antes = est.opcao_mei.isin(["S", "N"]) & mei_ini.notna()
pequeno = est.porte.isin(["01", "03"]) | est.opcao_mei.eq("S")  # ME, EPP ou MEI
# Natureza 213-5 = empresário individual (forma jurídica do MEI)

# aberturas e baixas: contagens por mês do evento
ev = pd.DataFrame({"cod_ibge": est.cod_ibge})
linhas = []
def conta(nome, mask, periodo):
    s = ev[mask].groupby([ev.cod_ibge[mask], periodo[mask]]).size()
    s.index.names = ["cod_ibge", "mes"]
    return s.rename(nome)

linhas.append(conta("aberturas_cnpj", ini_m.notna(), ini_m))
linhas.append(conta("aberturas_matriz", est.matriz & ini_m.notna(), ini_m))
# novo MEI: CNPJ aberto que optou pelo MEI no mesmo mês da abertura
# (equivale à formalização de um MEI no Portal do Empreendedor)
novo_mei = eh_mei_hoje_ou_antes & (mei_ini == ini_m)
linhas.append(conta("aberturas_mei", novo_mei, ini_m))
# qualquer opção pelo MEI no mês (inclui empresas já existentes)
linhas.append(conta("opcoes_mei", eh_mei_hoje_ou_antes, mei_ini))
linhas.append(conta("aberturas_pequenos", pequeno & ini_m.notna(), ini_m))
linhas.append(conta("baixas_cnpj", est.situacao.eq(8) & sit_m.notna(), sit_m))
eventos = pd.concat(linhas, axis=1).fillna(0).astype(int).reset_index()

# estoques no fim de cada mês
est_ativo = []
for m in MESES:
    ativo = (ini_m <= m) & (est.situacao.eq(2) | (sit_m > m))
    mei_at = ativo & eh_mei_hoje_ou_antes & (mei_ini <= m) & (mei_fim.isna() | (mei_fim > m))
    sn_at = ativo & est.opcao_simples.isin(["S", "N"]) & (sn_ini <= m) & (sn_fim.isna() | (sn_fim > m))
    g = pd.DataFrame({"cod_ibge": est.cod_ibge, "ativas": ativo,
                      "ativas_matriz": ativo & est.matriz,
                      "ativas_mei": mei_at, "ativas_simples": sn_at,
                      "ativas_pequenos": ativo & pequeno})
    s = g.groupby("cod_ibge").sum()
    s["mes"] = m
    est_ativo.append(s.reset_index())
estoques = pd.concat(est_ativo, ignore_index=True)

painel = estoques.merge(eventos, on=["cod_ibge", "mes"], how="left").fillna(0)
painel["anomes"] = painel.mes.dt.year * 100 + painel.mes.dt.month
painel = painel.drop(columns="mes")
inteiras = [c for c in painel.columns if c not in ("cod_ibge", "anomes")]
painel[inteiras] = painel[inteiras].astype(int)
painel.to_csv(PROC / "cnpj_municipio_mes.csv", index=False)

# ----------------------------------------------------------------------------
# 5. Covariáveis pré-tratamento (dez/2019)
# ----------------------------------------------------------------------------
m19 = pd.Period("2019-12", "M")
ativo19 = (ini_m <= m19) & (est.situacao.eq(2) | (sit_m > m19))
ies = est[ativo19 & est.cnae.isin(CNAE_SUPERIOR)].groupby("cod_ibge").size()
base19 = painel[painel.anomes == 201912].set_index("cod_ibge")
cov19 = pd.DataFrame({
    "n_estab_ensino_superior_2019": ies,
    "pct_simples_2019": 100 * base19.ativas_simples / base19.ativas,
    "pct_mei_2019": 100 * base19.ativas_mei / base19.ativas,
}).reindex(base19.index).fillna({"n_estab_ensino_superior_2019": 0})
cov19["campus"] = (cov19.n_estab_ensino_superior_2019 > 0).astype(int)
cov19.reset_index().to_csv(PROC / "cnpj_municipio_2019.csv", index=False)
print(painel.shape, "| municípios:", painel.cod_ibge.nunique())
print(painel[painel.anomes.isin([201912, 202212, 202412])]
      .groupby("anomes")[["ativas", "ativas_mei", "aberturas_mei"]].sum())

# ----------------------------------------------------------------------------
# 6. Validação contra o Mapa de Empresas (MEMP), agosto/2026
#    (planilha mensal em gov.br/memp > Dados abertos)
# ----------------------------------------------------------------------------
import urllib.request

MAPA = RAIZ / "dados" / "brutos" / "memp" / "mapa_ago26.xlsx"
if not MAPA.exists():
    MAPA.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(
        "https://www.gov.br/memp/pt-br/acesso-a-informacao/dados-abertos/"
        "08_arquivodados_ago26-mapa-de-empresas.xlsx/@@download/file", MAPA)
mapa = pd.read_excel(MAPA, sheet_name="Abertas, Fechadas e Ativas",
                     usecols=range(7))
mapa = mapa.rename(columns={"cod_ibge": "cod6", "Empresas Abertas": "mapa_abertas",
                            "Empresas Ativas": "mapa_ativas",
                            "Empresas Fechadas": "mapa_fechadas"})
m26 = pd.Period("2026-08", "M")
val = pd.DataFrame({
    "cod_ibge": est.cod_ibge,
    "nossa_ativas": (ini_m <= m26) & (est.situacao.eq(2) | (sit_m > m26)),
    "nossa_abertas": ini_m == m26,
    "nossa_fechadas": est.situacao.eq(8) & (sit_m == m26),
}).groupby("cod_ibge").sum().reset_index()
val["cod6"] = val.cod_ibge // 10
val = val.merge(mapa[["cod6", "nome", "mapa_abertas", "mapa_fechadas", "mapa_ativas"]],
                on="cod6", how="left")
val["razao_ativas"] = val.nossa_ativas / val.mapa_ativas
val.to_csv(PROC / "validacao_mapa_empresas.csv", index=False)
print("\nValidação (ago/2026) — razão nossa/Mapa de Empresas, empresas ativas:")
print(val.razao_ativas.describe().round(3).to_string())
print("Correlação abertas:", round(val[["nossa_abertas", "mapa_abertas"]].corr().iloc[0, 1], 3))
