"""
03 - ESTBAN por município (Banco Central do Brasil), 2019-2024.

Fonte: https://www.bcb.gov.br/estatisticas/estatisticabancariamunicipios
Arquivos: .../estatistica_bancaria_estban/municipio/AAAAMM_ESTBAN.csv.zip
(padrão de URL conferido no pacote R `estbanr`, CRAN).

O arquivo é nacional, uma linha por instituição x município x mês, com os
saldos contábeis (verbetes COSIF) em R$.

Saídas:
  dados/processados/estban_banco_municipio_mes.csv  (MT, MS, GO; banco a banco)
  dados/processados/estban_municipio_mes.csv        (agregado por município)

Variáveis agregadas (município x mês):
  credito_total   = verbete 160 (operações de crédito; PF + PJ)
  emprestimos     = verbete 161 (empréstimos e títulos descontados)
  financiamentos  = verbete 162
  credito_rural   = verbete 163 + 167
  dep_vista       = verbetes 401 a 419 (depósitos à vista; o BCB publica
                    PF, PJ e governo agrupados numa só coluna)
  dep_poupanca    = verbete 420
  dep_prazo       = verbete 432
  n_instituicoes  = nº de instituições com crédito > 0
  n_agencias      = soma de AGEN_PROCESSADAS
  ihh_credito     = Herfindahl-Hirschman do crédito (verbete 160) entre
                    instituições, escala 0-1
  ihh_deposito    = idem para depósitos à vista
  estban_imputado = 1 se algum banco do município estava em "não-reporte"
                    naquele mês e teve o saldo imputado (ver abaixo)

ATENÇÃO 1: o ESTBAN não separa crédito a pessoas jurídicas e físicas. O
"crédito PJ" do artigo (Y3, Y5) é aproximado pelo crédito total (160) e,
os depósitos à vista também vêm agregados (PF+PJ+governo) no arquivo.

ATENÇÃO 2 (não-reporte): às vezes uma instituição aparece com TODOS os
verbetes zerados no país inteiro num mês (ex.: Santander, jan-mar/2025).
Isso não é saldo zero, é falha de envio. Detectamos esses casos no arquivo
nacional e imputamos o último saldo reportado da mesma instituição no mesmo
município (LOCF).

Execute de dentro de codigo/:  python 03_estban_bcb.py
"""
import io
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "estban"
PROC = RAIZ / "dados" / "processados"
BRUTOS.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

BASE = ("https://www.bcb.gov.br/content/estatisticas/"
        "estatistica_bancaria_estban/municipio/")
UFS = ["MT", "MS", "GO"]
MESES = [f"{a}{m:02d}" for a in range(2019, 2025) for m in range(1, 13)]
VERBETES = {"160": "credito_total", "161": "emprestimos",
            "162": "financiamentos", "163": "fin_rural", "167": "fin_agroind",
            "401": "dep_vista",
            "420": "dep_poupanca", "432": "dep_prazo"}


def baixar(ref):
    """Baixa o zip do mês (tenta as variantes de nome usadas pelo BCB)."""
    destino = BRUTOS / f"{ref}_ESTBAN.zip"
    if destino.exists() and destino.stat().st_size > 1000:
        return destino.read_bytes()
    for _ in range(4):
      for nome in (f"{ref}_ESTBAN.csv.zip", f"{ref}_ESTBAN.ZIP", f"{ref}_ESTBAN.zip"):
        for _ in range(2):
            try:
                time.sleep(3)  # gentileza com o servidor do BCB
                with urllib.request.urlopen(BASE + nome, timeout=300) as r:
                    dados = r.read()
                # o BCB às vezes devolve uma página de erro HTML com código 200
                if dados[:2] != b"PK" and b"#DATA_BASE" not in dados[:5000]:
                    time.sleep(15)
                    continue
                destino.write_bytes(dados)
                return dados
            except urllib.error.HTTPError as e:
                if e.code in (403, 404):
                    break
                time.sleep(10)
            except Exception:
                time.sleep(10)
    raise RuntimeError(f"ESTBAN {ref} não encontrado")


def ler(dados):
    """Lê o CSV (zipado ou não), devolve o arquivo nacional com nomes limpos."""
    if dados[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            dados = z.read(z.namelist()[0])
    texto = dados.decode("latin1")
    linhas = texto.splitlines()
    ini = next(i for i, l in enumerate(linhas) if l.startswith("#DATA_BASE"))
    df = pd.read_csv(io.StringIO("\n".join(linhas[ini:])), sep=";",
                     dtype=str)
    novos = {}
    for c in df.columns:
        if c.startswith("VERBETE_"):
            cod = c.split("_")[1]
            # 401 é publicado agrupado (401+402+...+411+412+...): é o total
            # de depósitos à vista; os demais devem ser colunas próprias.
            if cod in VERBETES and ("+" not in c or cod == "401"):
                novos[c] = VERBETES[cod]
    df = df.rename(columns=novos | {"#DATA_BASE": "anomes"})
    df.columns = [c.lower() if not c.startswith("VERBETE_") else c
                  for c in df.columns]
    return df, [v for v in novos.values()]


def numero(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False),
                         errors="coerce").fillna(0.0)


partes, faltando = [], {}
for ref in MESES:
    df, cols = ler(baixar(ref))
    faltando[ref] = sorted(set(VERBETES.values()) - set(cols))
    todos_verb = [c for c in df.columns if c.startswith("VERBETE_")] + cols
    for c in todos_verb:
        df[c] = numero(df[c])
    # não-reporte: instituição com todos os verbetes = 0 no país inteiro
    tot = df[todos_verb].abs().sum(axis=1).groupby(df["cnpj"]).transform("sum")
    df["nonreport"] = tot.eq(0)
    df = df[df["uf"].isin(UFS)].copy()
    for c in VERBETES.values():
        if c not in df.columns:
            df[c] = np.nan
    df["anomes"] = int(ref)
    if "codmun_ibge" not in df.columns:
        df["codmun_ibge"] = np.nan
    df["agen_processadas"] = numero(df["agen_processadas"])
    partes.append(df[["anomes", "uf", "codmun", "codmun_ibge", "municipio", "cnpj",
                      "nome_instituicao", "agen_processadas", "nonreport"]
                     + list(VERBETES.values())])
    print(ref, len(df), "linhas", "| não-reporte:",
          df.loc[df.nonreport, "nome_instituicao"].unique()[:3])

banco = pd.concat(partes, ignore_index=True)
banco = banco.sort_values(["codmun", "cnpj", "anomes"])

# Imputação LOCF dos meses de não-reporte
vals = list(VERBETES.values())
banco.loc[banco.nonreport, vals] = np.nan
banco[vals] = banco.groupby(["codmun", "cnpj"])[vals].ffill()
banco[vals] = banco[vals].fillna(0.0)
banco.to_csv(PROC / "estban_banco_municipio_mes.csv", index=False)


def ihh(x):
    x = x[x > 0]
    return float(((x / x.sum()) ** 2).sum()) if x.sum() > 0 else np.nan


# o código IBGE só aparece nos arquivos mais recentes: propaga pelo codmun
banco["codmun_ibge"] = pd.to_numeric(banco["codmun_ibge"], errors="coerce")
banco["codmun_ibge"] = banco.groupby("codmun")["codmun_ibge"].transform("max")
# o nome do município pode variar de grafia entre arquivos: fixa o último
banco["municipio"] = banco.groupby("codmun")["municipio"].transform("last")
g = banco.groupby(["uf", "codmun", "codmun_ibge", "municipio", "anomes"],
                  dropna=False)
mun = g[vals + ["agen_processadas"]].sum().rename(
    columns={"agen_processadas": "n_agencias"})
mun["credito_rural"] = mun.pop("fin_rural") + mun.pop("fin_agroind")
mun["n_instituicoes"] = g["credito_total"].apply(lambda s: int((s > 0).sum()))
mun["ihh_credito"] = g["credito_total"].apply(ihh)
mun["ihh_deposito"] = g["dep_vista"].apply(ihh)
mun["estban_imputado"] = g["nonreport"].max().astype(int)
mun = mun.reset_index()
mun.to_csv(PROC / "estban_municipio_mes.csv", index=False)
print(mun.shape, "| verbetes ausentes por mês:",
      {k: v for k, v in faltando.items() if v})
