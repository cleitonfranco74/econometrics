"""Gera os arquivos casos_dados.js usados pelos exploradores interativos das páginas.

Uso:  python preparar_web.py   (requer pandas, openpyxl; e o resultado de
06-diferencas-em-diferencas/codigo/casos_did.py para o Conteúdo 6)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
STATS = AQUI.parent


def js(variavel, obj, destino):
    texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    destino.write_text(f"// Gerado por dados_caso/preparar_web.py — não edite à mão.\nwindow.{variavel}={texto};\n",
                       encoding="utf-8")
    print(destino.relative_to(STATS), f"{destino.stat().st_size // 1024} KB")


def tabela(df, rotulo):
    df = df.dropna()
    return {"rotulo": rotulo, "vars": list(df.columns),
            "dados": [[round(float(v), 4) for v in df[c]] for c in df.columns]}


# ---------------- Conteúdo 3: correlação e regressão simples ----------------
c3 = {}
x = pd.ExcelFile(AQUI / "correlacoes_empresariais.xlsx")
nomes = {"Apple": "Apple (mensal, 2019–2023)", "Netflix": "Netflix (trimestral, 2018–2024)",
         "CocaCola": "Coca-Cola (80 regiões)", "Tesla": "Tesla (mensal, 2018–2023)",
         "Tarifaço": "Tarifaço: exportações (mensal, 2017–2023)", "Tesla_BYD": "Tesla × BYD (mensal, 2019–2023)"}
for aba, rot in nomes.items():
    d = x.parse(aba).select_dtypes("number")
    c3[aba] = tabela(d, rot)
g = pd.read_excel(AQUI / "google_reglinear.xlsx").select_dtypes("number")
c3["Google"] = tabela(g, "Google (mensal, 2019–2023)")
gm = pd.read_stata(AQUI / "gini_pib_mundo.dta")
u = gm[gm.year == 2019].assign(lpib=lambda v: np.log(v.gdppercapita))
c3["Gini"] = tabela(u[["gdppercapita", "lpib", "ginicoefficient"]].rename(columns={
    "gdppercapita": "PIB per capita (US$ PPC)", "lpib": "ln(PIB per capita)",
    "ginicoefficient": "Índice de Gini"}), "Gini × PIB per capita (152 países, 2019)")
c3["Gini"]["nomes"] = u.dropna()["entity"].tolist()
cc = pd.read_csv(AQUI / "coca_cola_regioes.csv").drop(columns=["Região", "Ano"])
cc.columns = ["Taxa de obesidade (%)", "Consumo de refrigerante (L/hab.)", "Índice de atividade física",
              "Renda per capita (mil US$)", "Preço do refrigerante (US$/L)", "Prevalência de diabetes (%)",
              "Índice de marketing", "População urbana (%)"]
c3["CocaPainel"] = tabela(cc, "Coca-Cola ampliada (80 regiões × 4 anos)")
js("CASOS3", c3, STATS / "03-correlacao-causalidade-regressao" / "casos_dados.js")

# ---------------- Conteúdo 4: laboratório de regressão múltipla ----------------
c4 = {}
x = pd.ExcelFile(AQUI / "estudos_caso_regressao_multipla.xlsx")
dic = x.parse("Dicionário", header=None).iloc[:, :5]
dic.columns = ["caso", "var", "desc", "papel", "origem"]
for aba in ["Amazon", "Google", "Microsoft", "Petrobras", "MercadoLivre"]:
    d = x.parse(aba)
    d = d.drop(columns=[c for c in d.columns if c == "Data" or str(c).startswith("log ")])
    info = dic[dic.caso == aba]
    y = info[info.papel.astype(str).str.contains("DEPEND")]["var"].iloc[0]
    t = tabela(d[[y] + [c for c in d.columns if c != y]], f"{aba} (mensal, jan/2019–dez/2023)")
    t["y"] = y
    t["nova"] = info[info.origem == "Nova"]["var"].tolist()
    c4[aba] = t
w = pd.read_stata(AQUI / "wage1.dta")
w = w[["LWAGE", "EDUC", "EXPER", "EXPERSQ", "TENURE", "TENURSQ", "FEMALE", "MARRIED", "NONWHITE", "NUMDEP", "SMSA"]]
w.columns = ["ln(salário-hora)", "Educação (anos)", "Experiência", "Experiência²", "Tempo de empresa",
             "Tempo de empresa²", "Mulher", "Casado(a)", "Não branco(a)", "Nº de dependentes", "Área metropolitana"]
t = tabela(w, "Salários — wage1 (Wooldridge), 526 trabalhadores")
t["y"] = "ln(salário-hora)"
c4["wage1"] = t
cc = pd.read_csv(AQUI / "coca_cola_regioes.csv").drop(columns=["Região", "Ano"])
cc.columns = ["Taxa de obesidade (%)", "Consumo de refrigerante (L/hab.)", "Índice de atividade física",
              "Renda per capita (mil US$)", "Preço do refrigerante (US$/L)", "Prevalência de diabetes (%)",
              "Índice de marketing", "População urbana (%)"]
t = tabela(cc, "Coca-Cola: obesidade em 80 regiões × 4 anos")
t["y"] = "Taxa de obesidade (%)"
c4["CocaCola"] = t
js("CASOS4", c4, STATS / "04-regressao-multipla" / "casos_dados.js")

# ---------------- Conteúdo 6: estudos de eventos ----------------
res = STATS / "06-diferencas-em-diferencas" / "codigo" / "casos_did_resultados.json"
if res.exists():
    js("CASOS6", json.loads(res.read_text()), STATS / "06-diferencas-em-diferencas" / "casos_dados.js")
else:
    print("Rode antes 06-diferencas-em-diferencas/codigo/casos_did.py")
