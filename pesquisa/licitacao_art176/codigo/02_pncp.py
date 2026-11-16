"""
02 - Contratações publicadas no PNCP por órgãos municipais do Paraná (2021-2026).

API pública de consulta: https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao
Modalidades (código PNCP):
   4 = Concorrência - Eletrônica     5 = Concorrência - Presencial
   6 = Pregão - Eletrônico           7 = Pregão - Presencial
Uso: medir a ADOÇÃO da forma eletrônica (primeiro estágio). O PNCP não serve
para desfechos: municípios de até 20 mil hab. estão dispensados de publicar
nele até abr/2027 (art. 176), o que geraria seleção mecânica.

Saída: dados/processados/pncp_compras_pr.csv (uma linha por compra)
Execute de dentro de codigo/:  python 02_pncp.py
"""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "pncp"
PROC = RAIZ / "dados" / "processados"
BRUTOS.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

URL = ("https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?"
       "dataInicial={ini}&dataFinal={fim}&codigoModalidadeContratacao={mod}"
       "&uf=PR&pagina={pag}&tamanhoPagina=50")
MODS = [4, 5, 6, 7]
MESES = pd.period_range("2021-04", "2026-10", freq="M")  # PNCP começa em 2021


def pega(url):
    for t in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                if r.status == 204:
                    return {"data": [], "totalPaginas": 0}
                return json.loads(r.read() or b'{"data": [], "totalPaginas": 0}')
        except Exception:
            time.sleep(5 * (t + 1))
    raise RuntimeError(url)


def campos(x):
    u, o = x.get("unidadeOrgao") or {}, x.get("orgaoEntidade") or {}
    return {"cod_ibge": u.get("codigoIbge"), "municipio": u.get("municipioNome"),
            "esfera": o.get("esferaId"), "cnpj_orgao": o.get("cnpj"),
            "orgao": o.get("razaoSocial"), "modalidade_id": x.get("modalidadeId"),
            "modalidade": x.get("modalidadeNome"), "modo_disputa": x.get("modoDisputaNome"),
            "srp": x.get("srp"), "ano_compra": x.get("anoCompra"),
            "data_publicacao": x.get("dataPublicacaoPncp"),
            "data_abertura": x.get("dataAberturaProposta"),
            "valor_estimado": x.get("valorTotalEstimado"),
            "valor_homologado": x.get("valorTotalHomologado"),
            "situacao": x.get("situacaoCompraNome"), "sistema": x.get("usuarioNome"),
            "objeto": (x.get("objetoCompra") or "")[:300],
            "numero_controle": x.get("numeroControlePNCP")}


def mes_mod(args):
    mes, mod = args
    arq = BRUTOS / f"{mes}_{mod}.jsonl"
    if arq.exists():
        return
    ini = mes.start_time.strftime("%Y%m%d")
    fim = mes.end_time.strftime("%Y%m%d")
    linhas, pag, total = [], 1, 1
    while pag <= total:
        d = pega(URL.format(ini=ini, fim=fim, mod=mod, pag=pag))
        total = d.get("totalPaginas", 0) or 0
        linhas += [campos(x) for x in d.get("data", [])
                   if (x.get("orgaoEntidade") or {}).get("esferaId") == "M"]
        pag += 1
    tmp = arq.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in linhas))
    tmp.rename(arq)
    print(mes, mod, len(linhas), flush=True)


tarefas = [(m, mod) for m in MESES for mod in MODS]
with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(mes_mod, tarefas))

regs = []
for f in sorted(BRUTOS.glob("*.jsonl")):
    regs += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
df = pd.DataFrame(regs).drop_duplicates("numero_controle")
df.to_csv(PROC / "pncp_compras_pr.csv", index=False)
print(df.shape, df.groupby("modalidade").size().to_dict())
