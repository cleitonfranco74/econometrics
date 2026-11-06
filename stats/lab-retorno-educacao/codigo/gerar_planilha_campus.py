"""Planilha do Exemplo 2 (campus federal e renda municipal), com fórmulas vivas."""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "dados" / "municipios_campus.csv")
N = len(df)
U = N + 1

F = "Arial"
TIT = Font(name=F, size=14, bold=True, color="1D2330")
H = Font(name=F, size=11, bold=True, color="FFFFFF")
B = Font(name=F, size=11, bold=True)
TX = Font(name=F, size=11)
NOTA = Font(name=F, size=10, italic=True, color="5B6475")
LINK = Font(name=F, size=11, color="1866A3", underline="single")
FILL_H = PatternFill("solid", fgColor="1866A3")
FILL_R = PatternFill("solid", fgColor="F2F0EA")
FILL_K = PatternFill("solid", fgColor="FBE9DF")
fino = Side(style="thin", color="DEDAD0")
BORDA = Border(left=fino, right=fino, top=fino, bottom=fino)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()
ws = wb.active
ws.title = "LEIA-ME"
ws.column_dimensions["A"].width = 22
ws.column_dimensions["B"].width = 95
txt = [
    ("Exemplo 2: campus federal e renda do município", None, TIT),
    ("Laboratório 'Vale a pena estudar?' · Prof. Cleiton Franco · UNEMAT", None, NOTA),
    ("", None, TX),
    ("Atenção", "Os 1.500 municípios são FICTÍCIOS. O efeito verdadeiro do campus é de 3,5% na renda per capita "
     "das cidades grandes e 7% nas pequenas (menos de 50 mil habitantes). Os campi foram instalados de "
     "propósito em cidades maiores, mais ricas e mais distantes da capital.", TX),
    ("Abas", "dados · 1_comparacao (médias e regressão simples) · 2_multipla (PROJ.LIN, modelos C1 a C4).", TX),
    ("Regra do Excel", "Para PROJ.LIN e para Dados > Análise de Dados > Regressão, as colunas de X precisam ser vizinhas. "
     "A aba 'dados' já está ordenada: L campus · M lrenda00 · N lpop · O urbanizacao_2000 · P dist100 · "
     "Q–T regiões · U campus_pequeno · V pequeno. Y = K (lrenda10).", TX),
    ("Erros-padrão", "O Excel calcula só os clássicos; os robustos (HC1) estão no script campus.inp do Gretl.", TX),
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
    ("municipio, regiao", "Identificador e região (dummies norte, nordeste, sul, centro_oeste; base = Sudeste)"),
    ("pop_2000, pequeno", "População em 2000; pequeno = 1 se menos de 50 mil habitantes"),
    ("urbanizacao_2000", "Taxa de urbanização em 2000 (0 a 1)"),
    ("dist_capital, dist100", "Distância à capital do estado em km e em centenas de km"),
    ("campus", "1 se recebeu campus federal novo na expansão dos anos 2000"),
    ("renda_pc_2000/2010", "Renda domiciliar per capita (R$ correntes do censo fictício)"),
    ("pobreza_2000/2010", "Pessoas pobres (% da população)"),
    ("lrenda00, lrenda10, lpop, dlrenda", "Calculadas por fórmula: logaritmos e crescimento (lrenda10 − lrenda00)"),
]:
    ws.cell(r, 1, nome).font = Font(name=F, size=11, bold=True, color="1866A3")
    c = ws.cell(r, 2, desc)
    c.font = TX
    c.alignment = WRAP
    r += 1

wd = wb.create_sheet("dados")
cols = ["municipio", "regiao", "pop_2000", "dist_capital", "renda_pc_2000", "renda_pc_2010",
        "pobreza_2000", "pobreza_2010", "dlrenda", "pequeno_txt", "lrenda10", "campus", "lrenda00",
        "lpop", "urbanizacao_2000", "dist100", "norte", "nordeste", "sul", "centro_oeste",
        "campus_pequeno", "pequeno"]
for j, nome in enumerate(cols, start=1):
    c = wd.cell(1, j, nome)
    c.font = H
    c.fill = FILL_H
    c.alignment = Alignment(horizontal="center")
    wd.column_dimensions[get_column_letter(j)].width = 13
formulas = {"dlrenda": "=K{i}-M{i}", "lrenda10": "=LN(F{i})", "lrenda00": "=LN(E{i})",
            "lpop": "=LN(C{i})", "dist100": "=D{i}/100", "campus_pequeno": "=L{i}*V{i}",
            "pequeno_txt": '=IF(V{i}=1,"pequeno","grande")'}
for i, row in enumerate(df.itertuples(index=False), start=2):
    d = row._asdict()
    for j, nome in enumerate(cols, start=1):
        if nome in formulas:
            wd.cell(i, j, formulas[nome].format(i=i))
        else:
            wd.cell(i, j, d[nome])
wd.freeze_panes = "A2"
X = lambda col: f"dados!${col}${2}:${col}${U}"

def linha(w, r, rot, f, fmt="0.0000", nota=None, destaque=False):
    w.cell(r, 1, rot).font = TX
    c = w.cell(r, 2, f)
    c.number_format = fmt
    c.border = BORDA
    c.font = B if destaque else TX
    if destaque:
        c.fill = FILL_K
    if nota:
        n = w.cell(r, 3, nota)
        n.font = NOTA
        n.alignment = WRAP

w1 = wb.create_sheet("1_comparacao")
w1.column_dimensions["A"].width = 44
w1.column_dimensions["B"].width = 16
w1.column_dimensions["C"].width = 16
w1.column_dimensions["D"].width = 60
w1["A1"] = "Antes de regredir: os dois grupos eram parecidos?"
w1["A1"].font = TIT
for j, t in enumerate(["Média", "Sem campus", "Com campus"], start=1):
    c = w1.cell(3, j, t)
    c.font = H
    c.fill = FILL_H
CAMP = X("L")
for k, (rot, col, fmt) in enumerate([("População em 2000", "C", "#,##0"),
                                     ("Renda per capita 2000 (R$)", "E", "#,##0.00"),
                                     ("Renda per capita 2010 (R$)", "F", "#,##0.00"),
                                     ("Distância à capital (km)", "D", "#,##0"),
                                     ("Urbanização 2000", "O", "0.000"),
                                     ("Pobreza 2010 (%)", "H", "0.0"),
                                     ("ln(renda 2010)", "K", "0.0000"),
                                     ("Crescimento da renda (dlrenda)", "I", "0.0000"),
                                     ("Nº de municípios", None, "0")], start=4):
    w1.cell(k, 1, rot).font = TX
    for j, g in ((2, 0), (3, 1)):
        f = (f"=COUNTIF({CAMP},{g})" if col is None else f"=AVERAGEIF({CAMP},{g},{X(col)})")
        c = w1.cell(k, j, f)
        c.number_format = fmt
        c.border = BORDA
        c.font = TX
w1["A15"] = "Regressão simples com uma dummy"
w1["A15"].font = TIT
linha(w1, 16, "C1: inclinação de lrenda10 em campus", f"=SLOPE({X('K')},{CAMP})", "0.0000",
      "É a diferença das médias de ln(renda 2010) entre os grupos (C10 − B10).", True)
linha(w1, 17, "Em %: e^b − 1", "=EXP(B16)-1", "0.0%")
linha(w1, 18, "Conferência: C10 − B10", "=C10-B10")
linha(w1, 19, "C5: inclinação de dlrenda em campus", f"=SLOPE({X('I')},{CAMP})", "0.0000",
      "Compara o crescimento, não o nível: elimina a diferença que já existia em 2000.", True)
linha(w1, 20, "Pobreza: inclinação de pobreza_2010 em campus", f"=SLOPE({X('H')},{CAMP})", "0.00",
      "Diferença ingênua em pontos percentuais.")
w1["A22"] = ("Pergunta: por que C1 é tão maior que C5? Compare as linhas 4 e 5 da tabela acima: "
             "os municípios com campus já eram mais ricos e maiores em 2000.")
w1["A22"].font = NOTA
w1.merge_cells("A22:D23")
w1["A22"].alignment = WRAP

w2 = wb.create_sheet("2_multipla")
w2.column_dimensions["A"].width = 24
for j in range(2, 15):
    w2.column_dimensions[get_column_letter(j)].width = 12.5
w2["A1"] = "Regressão múltipla com PROJ.LIN: y = lrenda10"
w2["A1"].font = TIT
w2["A2"] = ("PROJ.LIN devolve os coeficientes em ORDEM INVERSA à das colunas de X, com a constante por último. "
            "Linhas: coeficiente · erro-padrão clássico · R² e σ̂ · F e gl · SQE e SQR.")
w2["A2"].font = NOTA
w2["A2"].alignment = WRAP
w2.merge_cells("A2:L3")
w2.row_dimensions[2].height = 30
nomes = ["campus", "lrenda00", "lpop", "urbanizacao_2000", "dist100", "norte", "nordeste", "sul",
         "centro_oeste", "campus_pequeno", "pequeno"]
modelos = [("(C1) só campus", 1), ("(C2) + renda de 2000", 2),
           ("(C3) + população, urbanização, distância, região", 9), ("(C4) + interação com cidade pequena", 11)]
lin = 5
pos = {}
for titulo, k in modelos:
    w2.cell(lin, 1, titulo).font = B
    rot = list(reversed(nomes[:k])) + ["const"]
    for j, nm in enumerate(rot, start=2):
        c = w2.cell(lin + 1, j, nm)
        c.font = H
        c.fill = FILL_H
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i, t in enumerate(["coeficiente", "erro-padrão", "R² | σ̂", "F | gl", "SQE | SQR"]):
        w2.cell(lin + 2 + i, 1, t).font = TX
    ultima = get_column_letter(12 + k - 1)            # L é a 1ª coluna de X
    ref = f"B{lin+2}:{get_column_letter(k+2)}{lin+6}"
    w2[f"B{lin+2}"] = ArrayFormula(
        ref, f'=IFERROR(LINEST({X("K")},dados!$L$2:${ultima}${U},TRUE,TRUE),"")')
    for rr in range(lin + 2, lin + 7):
        for cc in range(2, k + 3):
            cel = w2.cell(rr, cc)
            cel.number_format = "0.00000"
            cel.border = BORDA
            cel.font = B if rr == lin + 2 else TX
            if rr == lin + 2:
                cel.fill = FILL_R
    ccamp = get_column_letter(2 + rot.index("campus"))
    w2[f"{ccamp}{lin+2}"].fill = FILL_K
    pos[titulo[:4]] = (lin, rot)
    lin += 9

l4, rot4 = pos["(C4)"]
ca = get_column_letter(2 + rot4.index("campus"))
ci = get_column_letter(2 + rot4.index("campus_pequeno"))
w2.cell(lin, 1, "Leitura de C4").font = TIT
linha(w2, lin + 1, "Efeito do campus: cidade grande", f"={ca}{l4+2}", "0.0000", "Verdadeiro: 0,035.")
linha(w2, lin + 2, "Efeito do campus: cidade pequena", f"={ca}{l4+2}+{ci}{l4+2}", "0.0000",
      "Verdadeiro: 0,070. Soma do coeficiente de campus com o da interação.", True)
l3, rot3 = pos["(C3)"]
c3 = get_column_letter(2 + rot3.index("campus"))
linha(w2, lin + 3, "Efeito médio estimado em C3 (%)", f"=EXP({c3}{l3+2})-1", "0.0%",
      "Compare com a literatura: 3,5% a 5,8% (Barbosa, Petterini e Ferreira, RAC 2020).")

out = BASE / "dados" / "campus_excel.xlsx"
wb.save(out)
print(out)
