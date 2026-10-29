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
# Exemplos clássicos dos slides (gerados por exemplos_slides.py)
sa = pd.read_csv(AQUI / "sorvete_afogamentos_aula.csv")
c3["SorveteAula"] = tabela(sa[["vendas_sorvetes", "afogamentos"]].rename(columns={
    "vendas_sorvetes": "Vendas de sorvetes", "afogamentos": "Número de afogamentos"}),
    "Sorvete × afogamentos (12 meses, dados da aula)")
c3["SorveteAula"]["tempo"] = sa["mes"].tolist()
sm = pd.read_csv(AQUI / "salario_minimo_cesta_basica.csv")
c3["Salario"] = tabela(sm[["cesta_basica", "salario_minimo"]].rename(columns={
    "cesta_basica": "Cesta básica (R$)", "salario_minimo": "Salário mínimo (R$)"}),
    "Salário mínimo × cesta básica (jan/2018–out/2021)")
c3["Salario"]["tempo"] = sm["mes"].tolist()
vo = pd.read_csv(AQUI / "vacinacao_obitos.csv")
c3["Vacina"] = tabela(vo[["pct_vacinados_esquema_completo", "obitos"]].rename(columns={
    "pct_vacinados_esquema_completo": "% vacinados (esquema completo)", "obitos": "Número de óbitos"}),
    "Vacinação × óbitos (10 meses)")
c3["Vacina"]["tempo"] = vo["mes"].tolist()
sv = pd.read_csv(AQUI / "sorvete_afogamentos.csv")
c3["Sorvete"] = tabela(sv[["temperatura_media_c", "sorvetes_mil_unid", "afogamentos"]].rename(columns={
    "temperatura_media_c": "Temperatura média (°C)", "sorvetes_mil_unid": "Vendas de sorvete (mil unid.)",
    "afogamentos": "Afogamentos"}), "Sorvete × afogamentos com temperatura (ilustrativo, 36 meses)")
c3["Sorvete"]["tempo"] = sv["mes"].tolist()
mg = pd.read_csv(AQUI / "margarina_divorcio_maine.csv")
c3["Margarina"] = tabela(mg[["margarina_lb_per_capita_eua", "divorcios_por_mil_maine"]].rename(columns={
    "margarina_lb_per_capita_eua": "Consumo de margarina (lb/hab., EUA)",
    "divorcios_por_mil_maine": "Divórcios por mil hab. (Maine)"}), "Espúria: margarina × divórcio (2000–2009)")
c3["Margarina"]["tempo"] = mg["ano"].astype(str).tolist()
ng = pd.read_csv(AQUI / "nicolas_cage_afogamentos.csv")
c3["Cage"] = tabela(ng[["filmes_nicolas_cage", "afogamentos_em_piscina_eua"]].rename(columns={
    "filmes_nicolas_cage": "Filmes com Nicolas Cage", "afogamentos_em_piscina_eua": "Afogamentos em piscina (EUA)"}),
    "Espúria: Nicolas Cage × afogamentos (1999–2009)")
c3["Cage"]["tempo"] = ng["ano"].astype(str).tolist()
ct = pd.read_csv(AQUI / "carga_tributaria_gini.csv")
c3["Carga"] = tabela(ct[["gini", "carga_tributaria_pib"]].rename(columns={
    "gini": "Índice de Gini", "carga_tributaria_pib": "Carga tributária (% do PIB)"}),
    "Carga tributária × Gini (17 países)")
c3["Carga"]["nomes"] = ct["pais"].tolist()
sd = pd.read_csv(AQUI / "gasto_saude_suicidio_ocde.csv")
c3["Saude"] = tabela(sd[["gasto_saude_pc_usd_ppp", "suicidio_por_100mil"]].rename(columns={
    "gasto_saude_pc_usd_ppp": "Gasto em saúde per capita (US$ PPC)", "suicidio_por_100mil": "Suicídios por 100 mil hab."}),
    "Gasto em saúde × suicídio (12 países da OCDE)")
c3["Saude"]["nomes"] = sd["pais"].tolist()
ordem = ["SorveteAula", "Sorvete", "Margarina", "Cage", "Carga", "Salario", "Vacina", "Gini", "Saude", "Apple", "Netflix", "CocaCola", "Tesla",
         "Tarifaço", "Tesla_BYD", "Google", "CocaPainel"]
c3 = {k: c3[k] for k in ordem}
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
