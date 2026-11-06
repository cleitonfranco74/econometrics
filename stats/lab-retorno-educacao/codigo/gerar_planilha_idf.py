"""Planilha do Caso 3 (IDF-MT): o índice é construído inteiramente com fórmulas."""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "dados" / "idf_mt.csv")
N = len(df)
U = N + 1

F = "Arial"
TIT = Font(name=F, size=14, bold=True, color="1D2330")
H = Font(name=F, size=11, bold=True, color="FFFFFF")
B = Font(name=F, size=11, bold=True)
TX = Font(name=F, size=11)
NOTA = Font(name=F, size=10, italic=True, color="5B6475")
LINK = Font(name=F, size=11, color="1866A3", underline="single")
INPUT = Font(name=F, size=11, color="0000FF")
FILL_H = PatternFill("solid", fgColor="1866A3")
FILL_N = PatternFill("solid", fgColor="5B6475")
FILL_I = PatternFill("solid", fgColor="B5562A")
FILL_R = PatternFill("solid", fgColor="F2F0EA")
FILL_K = PatternFill("solid", fgColor="FBE9DF")
FILL_Y = PatternFill("solid", fgColor="FFFF00")
fino = Side(style="thin", color="DEDAD0")
BORDA = Border(left=fino, right=fino, top=fino, bottom=fino)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()

# ---------------------------------------------------------------------------
# LEIA-ME
# ---------------------------------------------------------------------------
ws = wb.active
ws.title = "LEIA-ME"
ws.column_dimensions["A"].width = 24
ws.column_dimensions["B"].width = 95
txt = [
    ("Caso 3: IDF-MT", None, TIT),
    ("Índice de condições digitais e financeiras dos pequenos negócios · Laboratório 'Vale a pena estudar?' · "
     "Prof. Cleiton Franco · UNEMAT", None, NOTA),
    ("", None, TX),
    ("Atenção", "Os 142 municípios são FICTÍCIOS. Os indicadores imitam fontes públicas (Anatel, Banco Central, "
     "Receita Federal, IBGE, SEBRAE/SENAR), mas os valores foram simulados.", TX),
    ("Pergunta", "Municípios com melhores condições digitais e financeiras têm pequenos negócios que usam mais o Pix?", TX),
    ("Abas", "dados (indicadores e o índice calculado por fórmula) · 1_indice (pesos e resumo) · "
     "2_validacao (regressões) · aux_X (cópia de colunas para o PROJ.LIN).", TX),
    ("Como o índice é feito", "1) cada indicador vira um número de 0 a 1: (x − mínimo) / (máximo − mínimo). "
     "2) Cada dimensão é a média dos seus indicadores, de 0 a 100. 3) O IDF é a média ponderada das três "
     "dimensões. Os pesos ficam nas células amarelas da aba 1_indice: mude-os e veja o ranking mudar.", TX),
    ("Erros-padrão", "O Excel calcula só os clássicos. Os robustos estão no script idf.inp do Gretl.", TX),
    ("Gretl (gratuito)", "Baixe o Gretl para Windows:", TX),
]
r = 1
for a, b, fonte in txt:
    ws.cell(r, 1, a).font = fonte if b is None else B
    if b is not None:
        c = ws.cell(r, 2, b)
        c.font = fonte
        c.alignment = WRAP
    r += 1
c = ws.cell(r - 1, 2, "gretl para Windows")
c.hyperlink = "https://gretl.sourceforge.net/win32/index_pt.html"
c.font = LINK
r += 1
ws.cell(r, 1, "Dicionário").font = TIT
r += 1
for nome, desc in [
    ("mesorregiao", "Mesorregião de Mato Grosso"),
    ("pop, pib_pc", "População e PIB per capita (R$)"),
    ("banda_larga", "Dimensão digital: acessos de banda larga fixa por 100 domicílios (fonte real equivalente: Anatel)"),
    ("cobertura_4g", "Dimensão digital: % da população coberta por 4G (Anatel)"),
    ("agencias", "Dimensão financeira: agências, postos e correspondentes por 10 mil hab. (Banco Central)"),
    ("cooperativa", "Dimensão financeira: 1 se há cooperativa de crédito no município (Banco Central)"),
    ("escolaridade", "Capacidades: anos médios de estudo dos adultos (IBGE, Censo)"),
    ("capacitacao", "Capacidades: participantes em cursos de gestão por 100 empresas (SEBRAE, SENAR)"),
    ("mei_mil", "Capacidades: microempreendedores individuais por mil hab. (Receita Federal)"),
    ("pix_pj", "Resultado: transações Pix recebidas por empresa por mês (Banco Central)"),
]:
    ws.cell(r, 1, nome).font = Font(name=F, size=11, bold=True, color="1866A3")
    c = ws.cell(r, 2, desc)
    c.font = TX
    c.alignment = WRAP
    r += 1

# ---------------------------------------------------------------------------
# 1_indice: pesos (entradas) — criada antes de 'dados' para ser referenciada
# ---------------------------------------------------------------------------
wi = wb.create_sheet("1_indice")
wd = wb.create_sheet("dados")
wb.move_sheet("dados", offset=-1)

wi.column_dimensions["A"].width = 30
for col in "BCDEF":
    wi.column_dimensions[col].width = 16
wi["A1"] = "Construção do IDF-MT"
wi["A1"].font = TIT
wi["A3"] = "Pesos das dimensões (devem somar 1)"
wi["A3"].font = B
pesos = [("Digital", 1 / 3), ("Financeira", 1 / 3), ("Capacidades", 1 / 3)]
for i, (nome, p) in enumerate(pesos, start=4):
    wi.cell(i, 1, nome).font = TX
    c = wi.cell(i, 2, "=1/3")
    c.font = INPUT
    c.fill = FILL_Y
    c.number_format = "0.000"
    c.border = BORDA
wi["A7"] = "Soma dos pesos"
wi["A7"].font = TX
wi["B7"] = "=SUM(B4:B6)"
wi["B7"].number_format = "0.000"
wi["C4"] = "Altere as células amarelas. Experimente dar peso 0,5 à dimensão digital."
wi["C4"].font = NOTA

# ---------------------------------------------------------------------------
# dados: indicadores + normalização + dimensões + índice, tudo em fórmulas
# ---------------------------------------------------------------------------
brutas = ["municipio", "mesorregiao", "pop", "pib_pc", "pix_pj"]
indic = ["banda_larga", "cobertura_4g", "agencias", "cooperativa", "escolaridade", "capacitacao", "mei_mil"]
# A-E brutas, F-L indicadores, M lpop, N lpib, O lpix, P-V normalizados, W-Y dimensões, Z idf, AA ranking
cab = brutas + indic + ["lpop", "lpib", "lpix"] + [f"n_{c}" for c in indic] + \
      ["dim_digital", "dim_financeira", "dim_capacidades", "idf", "ranking"]
for j, nome in enumerate(cab, start=1):
    c = wd.cell(1, j, nome)
    c.font = H
    c.fill = FILL_N if nome.startswith("n_") else (FILL_I if nome in ("idf", "ranking") or nome.startswith("dim_") else FILL_H)
    c.alignment = Alignment(horizontal="center")
    wd.column_dimensions[get_column_letter(j)].width = 12.5
col = {nome: get_column_letter(j) for j, nome in enumerate(cab, start=1)}
for i, row in enumerate(df.itertuples(index=False), start=2):
    d = row._asdict()
    for nome in brutas + indic:
        wd[f"{col[nome]}{i}"] = d[nome]
    wd[f"{col['lpop']}{i}"] = f"=LN({col['pop']}{i})"
    wd[f"{col['lpib']}{i}"] = f"=LN({col['pib_pc']}{i})"
    wd[f"{col['lpix']}{i}"] = f"=LN({col['pix_pj']}{i})"
    for c in indic:
        x = col[c]
        rng = f"${x}$2:${x}${U}"
        wd[f"{col['n_' + c]}{i}"] = f"=({x}{i}-MIN({rng}))/(MAX({rng})-MIN({rng}))"
    n = lambda c: f"{col['n_' + c]}{i}"
    wd[f"{col['dim_digital']}{i}"] = f"=100*AVERAGE({n('banda_larga')},{n('cobertura_4g')})"
    wd[f"{col['dim_financeira']}{i}"] = f"=100*AVERAGE({n('agencias')},{n('cooperativa')})"
    wd[f"{col['dim_capacidades']}{i}"] = f"=100*AVERAGE({n('escolaridade')},{n('capacitacao')},{n('mei_mil')})"
    wd[f"{col['idf']}{i}"] = (f"=('1_indice'!$B$4*{col['dim_digital']}{i}+'1_indice'!$B$5*{col['dim_financeira']}{i}"
                              f"+'1_indice'!$B$6*{col['dim_capacidades']}{i})/'1_indice'!$B$7")
    wd[f"{col['ranking']}{i}"] = f"=RANK({col['idf']}{i},${col['idf']}$2:${col['idf']}${U},0)"
    for nome in [f"n_{c}" for c in indic] + ["lpop", "lpib", "lpix"]:
        wd[f"{col[nome]}{i}"].number_format = "0.000"
    for nome in ["dim_digital", "dim_financeira", "dim_capacidades", "idf"]:
        wd[f"{col[nome]}{i}"].number_format = "0.0"
wd.freeze_panes = "C2"
R = lambda nome: f"dados!${col[nome]}$2:${col[nome]}${U}"

# resumo do índice na 1_indice
wi["A9"] = "Resumo do IDF-MT"
wi["A9"].font = B
for k, (rot, f) in enumerate([("Média", f"=AVERAGE({R('idf')})"), ("Mínimo", f"=MIN({R('idf')})"),
                              ("Máximo", f"=MAX({R('idf')})"), ("Desvio-padrão", f"=STDEV({R('idf')})")], start=10):
    wi.cell(k, 1, rot).font = TX
    c = wi.cell(k, 2, f)
    c.number_format = "0.0"
    c.border = BORDA
wi["A15"] = "IDF médio por mesorregião"
wi["A15"].font = B
for k, m in enumerate(["Norte", "Nordeste", "Sudoeste", "Centro-Sul", "Sudeste"], start=16):
    wi.cell(k, 1, m).font = TX
    c = wi.cell(k, 2, f'=AVERAGEIF({R("mesorregiao")},A{k},{R("idf")})')
    c.number_format = "0.0"
    c.border = BORDA
wi["A22"] = "Correlação do IDF com…"
wi["A22"].font = B
for k, (rot, v) in enumerate([("ln(população)", "lpop"), ("ln(PIB per capita)", "lpib"),
                              ("ln(Pix por empresa)", "lpix")], start=23):
    wi.cell(k, 1, rot).font = TX
    c = wi.cell(k, 2, f"=CORREL({R('idf')},{R(v)})")
    c.number_format = "0.00"
    c.border = BORDA
wi["C23"] = "Municípios maiores e mais ricos têm índice maior: cuidado ao interpretar a regressão simples."
wi["C23"].font = NOTA

# ---------------------------------------------------------------------------
# aux_X: colunas vizinhas para o PROJ.LIN do modelo I2 (idf, lpop, lpib)
# ---------------------------------------------------------------------------
aux = wb.create_sheet("aux_X")
for j, nome in enumerate(["idf", "lpop", "lpib"], start=1):
    c = aux.cell(1, j, nome)
    c.font = H
    c.fill = FILL_H
    for i in range(2, U + 1):
        aux.cell(i, j, f"=dados!{col[nome]}{i}")

# ---------------------------------------------------------------------------
# 2_validacao
# ---------------------------------------------------------------------------
wv = wb.create_sheet("2_validacao")
wv.column_dimensions["A"].width = 30
for j in range(2, 13):
    wv.column_dimensions[get_column_letter(j)].width = 13
wv["A1"] = "Validação: o índice explica o uso de Pix pelas empresas?"
wv["A1"].font = TIT

def linha(r, rot, f, fmt="0.0000", nota=None, destaque=False):
    wv.cell(r, 1, rot).font = TX
    c = wv.cell(r, 2, f)
    c.number_format = fmt
    c.border = BORDA
    c.font = B if destaque else TX
    if destaque:
        c.fill = FILL_K
    if nota:
        n = wv.cell(r, 3, nota)
        n.font = NOTA

wv["A3"] = "(I1) Regressão simples: ln(Pix) = a + b × IDF"
wv["A3"].font = B
linha(4, "b (INCLINAÇÃO)", f"=SLOPE({R('lpix')},{R('idf')})", "0.0000", None, True)
linha(5, "a (INTERCEPÇÃO)", f"=INTERCEPT({R('lpix')},{R('idf')})")
linha(6, "R²", f"=RSQ({R('lpix')},{R('idf')})", "0.000")
linha(7, "Efeito de +10 pontos no IDF", "=EXP(10*B4)-1", "0.0%", "Leitura: 10 pontos a mais no índice, quanto a mais de Pix por empresa.")

def bloco(ini, titulo, faixa_x, nomes):
    k = len(nomes)
    wv.cell(ini, 1, titulo).font = B
    rot = list(reversed(nomes)) + ["const"]
    for j, nm in enumerate(rot, start=2):
        c = wv.cell(ini + 1, j, nm)
        c.font = H
        c.fill = FILL_H
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i, t in enumerate(["coeficiente", "erro-padrão", "R² | σ̂", "F | gl", "SQE | SQR"]):
        wv.cell(ini + 2 + i, 1, t).font = TX
    ref = f"B{ini+2}:{get_column_letter(k+2)}{ini+6}"
    wv[f"B{ini+2}"] = ArrayFormula(ref, f'=IFERROR(LINEST({R("lpix")},{faixa_x},TRUE,TRUE),"")')
    for rr in range(ini + 2, ini + 7):
        for cc in range(2, k + 3):
            cel = wv.cell(rr, cc)
            cel.number_format = "0.0000"
            cel.border = BORDA
            cel.font = B if rr == ini + 2 else TX
            if rr == ini + 2:
                cel.fill = FILL_R
    return rot

wv["A9"] = ("PROJ.LIN devolve os coeficientes em ORDEM INVERSA à das colunas, com a constante por último. "
            "Linhas: coeficiente · erro-padrão · R² e σ̂ · F e gl · SQE e SQR.")
wv["A9"].font = NOTA
wv["A9"].alignment = WRAP
wv.merge_cells("A9:K10")
rot2 = bloco(12, "(I2) Mesmo tamanho e mesma riqueza: ln(Pix) em IDF, ln(pop), ln(PIB pc)",
             f"aux_X!$A$2:$C${U}", ["idf", "lpop", "lpib"])
ci = get_column_letter(2 + rot2.index("idf"))
linha(19, "Efeito de +10 pontos no IDF (I2)", f"=EXP(10*{ci}14)-1", "0.0%",
      "Compare com a linha 7: o efeito cai pela metade quando comparamos municípios parecidos.", True)
x0, x1 = col["banda_larga"], col["lpib"]
rot4 = bloco(22, "(I4) Qual parte do índice importa? ln(Pix) em cada indicador + controles",
             f"dados!${x0}$2:${x1}${U}", indic + ["lpop", "lpib"])
wv["A29"] = ("Leitura: banda larga, cooperativa e capacitação aumentam o uso de Pix. Pontos de atendimento, "
             "cobertura 4G, escolaridade e MEI não fazem diferença depois dos controles. Revisão do artefato (DSR): "
             "repensar os indicadores ou os pesos da dimensão financeira.")
wv["A29"].font = NOTA
wv["A29"].alignment = WRAP
wv.merge_cells("A29:K31")

out = BASE / "dados" / "idf_excel.xlsx"
wb.save(out)
print(out)
