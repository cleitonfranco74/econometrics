"""
02 - ISS mensal por município (SICONFI/Tesouro), jan/2023 a dez/2025.

Fonte: RREO - Anexo 03 (Demonstrativo da Receita Corrente Líquida), 6º
bimestre de cada ano. Esse anexo traz a arrecadação MÊS A MÊS dos últimos 12
meses (colunas <MR-11> ... <MR>), linha "ISS" (ISSLiquidoExcetoTransferenciasEFUNDEB).
API: https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo

Saída: dados/processados/iss_municipio_mes.csv  (cod_ibge, anomes, iss)
"""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "dados" / "brutos" / "siconfi_rreo3"
PROC = RAIZ / "dados" / "processados"
CACHE.mkdir(parents=True, exist_ok=True)
URL = ("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo?an_exercicio={a}"
       "&nr_periodo=6&co_tipo_demonstrativo=RREO&no_anexo=RREO-Anexo%2003"
       "&co_esfera=M&id_ente={m}")
ANOS = (2023, 2024, 2025)


def get(url):
    for t in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(3 * (t + 1))
    return None


def baixa(args):
    mun, ano = args
    arq = CACHE / f"{mun}_{ano}.json"
    if arq.exists():
        return
    d = get(URL.format(a=ano, m=mun))
    if d is None:
        return
    itens = [x for x in d.get("items", [])
             if x["cod_conta"] == "ISSLiquidoExcetoTransferenciasEFUNDEB"
             and x["coluna"].startswith("<MR")]
    arq.write_text(json.dumps(itens))


# lista de municípios (IBGE)
with urllib.request.urlopen("https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2024",
                            timeout=300) as r:
    muns = sorted({int(x["D1C"]) for x in json.loads(r.read())[1:]})
print(len(muns), "municípios")

with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(baixa, [(m, a) for m in muns for a in ANOS]))

linhas = []
for f in CACHE.glob("*.json"):
    mun, ano = map(int, f.stem.split("_"))
    for x in json.loads(f.read_text()):
        col = x["coluna"].strip("<>")                 # MR, MR-1, ..., MR-11
        k = 0 if col == "MR" else int(col.split("-")[1])
        mes = 12 - k
        linhas.append((mun, ano * 100 + mes, x["valor"]))
iss = pd.DataFrame(linhas, columns=["cod_ibge", "anomes", "iss"])
iss = iss.groupby(["cod_ibge", "anomes"], as_index=False).iss.sum()
iss.to_csv(PROC / "iss_municipio_mes.csv", index=False)
print(iss.shape, iss.cod_ibge.nunique(), "municípios com ISS")
