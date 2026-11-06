"""Monta a planilha do Laboratório para Excel (fórmulas vivas, sem valores fixos)."""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / "dados" / "pnad_simulada.csv")
N = len(df)
U = N + 1                                    # última linha de dados

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

# ---------------------------------------------------------------------------
# LEIA-ME
# ---------------------------------------------------------------------------
ws = wb.active
ws.title = "LEIA-ME"
ws.column_dimensions["A"].width = 22
ws.column_dimensions["B"].width = 95
linhas = [
    ("Laboratório: vale a pena estudar?", None, TIT),
    ("Regressão linear simples e múltipla · Prof. Cleiton Franco · UNEMAT", None, NOTA),
    ("", None, TX),
    ("Atenção", "Os 2.000 trabalhadores são FICTÍCIOS (dados simulados no estilo da PNAD Contínua). "
     "Os efeitos verdadeiros são conhecidos pelo professor, para comparar com as estimativas.", TX),
    ("Abas", "dados · 1_simples · 2_dummy · 3_multipla. Todas as contas são fórmulas: "
     "altere um dado e tudo se recalcula.", TX),
    ("Erros-padrão", "O Excel só calcula erros-padrão clássicos (supõem homocedasticidade). "
     "Os robustos (HC1) ficam no Gretl. Os coeficientes são idênticos nos dois programas.", TX),
    ("", None, TX),
    ("Ferramenta Regressão", "Para a saída completa (ANOVA, p-valores, IC), use Dados > Análise de Dados > Regressão. "
     "Se o botão não aparecer: Arquivo > Opções > Suplementos > Gerenciar: Suplementos do Excel > Ir > "
     "marque 'Ferramentas de Análise'.", TX),
    ("Passo a passo", "Intervalo Y de entrada: dados!$S$1:$S$2001 (lsal). Intervalo X de entrada: colunas "
     "vizinhas, por exemplo dados!$J$1:$M$2001 para o modelo M1 (educ, exper, exper2, mulher). "
     "Marque 'Rótulos' e escolha 'Nova planilha'.", TX),
    ("Regra do Excel", "As colunas de X precisam ser vizinhas. Por isso a aba 'dados' já está ordenada: "
     "J educ · K exper · L exper2 · M mulher · N norte · O nordeste · P sul · Q centro_oeste · "
     "R urbano · superior e habilidade nas colunas T e U.", TX),
    ("", None, TX),
    ("Gretl (gratuito)", "Baixe o Gretl para Windows:", TX),
]
r = 1
for a, b, fonte in linhas:
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
ws.cell(r, 1, "Dicionário de variáveis").font = TIT
r += 1
dic = [
    ("id", "Identificador do trabalhador"),
    ("regiao", "Região (texto). Dummies: norte, nordeste, sul, centro_oeste; base = Sudeste"),
    ("urbano", "1 se mora em área urbana"),
    ("mulher", "1 se mulher"),
    ("idade", "Idade em anos (25 a 64)"),
    ("educ", "Anos de estudo (0 a 20). 9 = fundamental, 12 = médio, 16 = superior"),
    ("nivel", "Nível de ensino concluído (texto). Dummies: fundamental, medio, superior; base = fund. incompleto"),
    ("exper", "Experiência potencial = idade − anos de estudo − 6"),
    ("educ_mae", "Anos de estudo da mãe"),
    ("horas", "Horas trabalhadas por semana"),
    ("salario_hora", "Salário por hora (R$)"),
    ("renda_mensal", "Renda do trabalho por mês (R$)"),
    ("habilidade", "Habilidade padronizada (média 0). Na vida real NÃO é observada; aqui é didática"),
    ("lsal, exper2", "Calculadas por fórmula: ln(salario_hora) e exper²"),
]
for nome, desc in dic:
    ws.cell(r, 1, nome).font = Font(name=F, size=11, bold=True, color="1866A3")
    c = ws.cell(r, 2, desc)
    c.font = TX
    c.alignment = WRAP
    r += 1

# ---------------------------------------------------------------------------
# dados — colunas ordenadas para o LINEST / ferramenta Regressão
# ---------------------------------------------------------------------------
wd = wb.create_sheet("dados")
cols = ["id", "regiao", "nivel", "idade", "educ_mae", "horas", "salario_hora",
        "renda_mensal", "fundamental", "educ", "exper", "exper2", "mulher", "norte",
        "nordeste", "sul", "centro_oeste", "urbano", "lsal", "superior", "habilidade", "medio"]
# I: fundamental  J: educ  K: exper  L: exper2  M: mulher  N–Q: regiões  R: urbano
# S: lsal  T: superior  U: habilidade  V: medio
for j, nome in enumerate(cols, start=1):
    c = wd.cell(1, j, nome)
    c.font = H
    c.fill = FILL_H
    c.alignment = Alignment(horizontal="center")
    wd.column_dimensions[get_column_letter(j)].width = 12.5
for i, row in enumerate(df.itertuples(index=False), start=2):
    d = row._asdict()
    for j, nome in enumerate(cols, start=1):
        if nome == "exper2":
            wd.cell(i, j, f"=K{i}^2")
        elif nome == "lsal":
            wd.cell(i, j, f"=LN(G{i})")
        else:
            wd.cell(i, j, d[nome])
for col in ("S",):
    for i in range(2, U + 1):
        wd[f"{col}{i}"].number_format = "0.0000"
wd.freeze_panes = "A2"
for celula in ("S1", "L1"):
    wd[celula].fill = PatternFill("solid", fgColor="B5562A")

X = lambda col: f"dados!${col}$2:${col}${U}"
Y_SAL, Y_L, EDUC = X("G"), X("S"), X("J")

def cabecalho(w, linha, textos, larguras=None):
    for j, t in enumerate(textos, start=1):
        c = w.cell(linha, j, t)
        c.font = H
        c.fill = FILL_H
        c.alignment = Alignment(horizontal="center", wrap_text=True)
        c.border = BORDA

def bloco(w, linha, rotulo, formula, fmt="0.0000", nota=None, destaque=False):
    w.cell(linha, 1, rotulo).font = TX
    c = w.cell(linha, 2, formula)
    c.font = B if destaque else TX
    c.number_format = fmt
    c.border = BORDA
    if destaque:
        c.fill = FILL_K
    if nota:
        n = w.cell(linha, 3, nota)
        n.font = NOTA
        n.alignment = WRAP

# ---------------------------------------------------------------------------
# 1_simples
# ---------------------------------------------------------------------------
w1 = wb.create_sheet("1_simples")
w1.column_dimensions["A"].width = 40
w1.column_dimensions["B"].width = 16
w1.column_dimensions["C"].width = 70
w1["A1"] = "Regressão simples: salário × anos de estudo"
w1["A1"].font = TIT
w1["A2"] = "Tudo calculado à mão com as fórmulas de MQO e conferido com as funções prontas do Excel."
w1["A2"].font = NOTA

def simples(w, ini, titulo, y, rot_y, interp):
    w.cell(ini, 1, titulo).font = B
    cabecalho(w, ini + 1, ["Quantidade", "Valor", "Como ler"])
    L = ini + 2
    bloco(w, L, "n", f"=COUNT({y})", "0")
    bloco(w, L + 1, f"Média de educ (x̄)", f"=AVERAGE({EDUC})")
    bloco(w, L + 2, f"Média de {rot_y} (ȳ)", f"=AVERAGE({y})")
    bloco(w, L + 3, "Σ(x−x̄)(y−ȳ)", f"=SUMPRODUCT(({EDUC}-B{L+1})*({y}-B{L+2}))", "#,##0.00")
    bloco(w, L + 4, "Σ(x−x̄)²", f"=DEVSQ({EDUC})", "#,##0.00")
    bloco(w, L + 5, "β̂₁ = Σ(x−x̄)(y−ȳ) / Σ(x−x̄)²", f"=B{L+3}/B{L+4}", "0.0000",
          interp, destaque=True)
    bloco(w, L + 6, "β̂₀ = ȳ − β̂₁·x̄", f"=B{L+2}-B{L+5}*B{L+1}")
    bloco(w, L + 7, "Conferência: INCLINAÇÃO()", f"=SLOPE({y},{EDUC})", "0.0000",
          "Função pronta. Deve ser igual a β̂₁.")
    bloco(w, L + 8, "Conferência: INTERCEPÇÃO()", f"=INTERCEPT({y},{EDUC})")
    bloco(w, L + 9, "R² = RQUAD()", f"=RSQ({y},{EDUC})", "0.000",
          "Fração da variação de y explicada pela educação.")
    bloco(w, L + 10, "Correlação r (r² = R²)", f"=CORREL({y},{EDUC})", "0.000")
    bloco(w, L + 11, "σ̂ = EPADYX()", f"=STEYX({y},{EDUC})", "0.0000",
          "Desvio-padrão dos resíduos.")
    bloco(w, L + 12, "ep(β̂₁) = σ̂ / √Σ(x−x̄)²", f"=B{L+11}/SQRT(B{L+4})", "0.0000",
          "Erro-padrão clássico (o Gretl também mostra o robusto).")
    bloco(w, L + 13, "t = β̂₁ / ep(β̂₁)", f"=B{L+5}/B{L+12}", "0.00",
          "|t| > 1,96 → rejeita β₁ = 0 a 5%.")
    bloco(w, L + 14, "IC 95%: limite inferior", f"=B{L+5}-1.96*B{L+12}")
    bloco(w, L + 15, "IC 95%: limite superior", f"=B{L+5}+1.96*B{L+12}")
    return L

L1 = simples(w1, 4, "(S1) Nível–nível: salario_hora = β₀ + β₁·educ + u", Y_SAL, "salario_hora",
             "Cada ano de estudo a mais está associado a β̂₁ reais a mais por hora.")
L2 = simples(w1, 23, "(S2) Log–nível: ln(salario_hora) = β₀ + β₁·educ + u", Y_L, "lsal",
             "100·β̂₁ ≈ variação % do salário por ano de estudo.")
bloco(w1, L2 + 16, "Variação % exata = 100·(e^β̂₁ − 1)", f"=100*(EXP(B{L2+5})-1)", "0.0",
      "A aproximação 100·β̂₁ piora quando β̂₁ é grande.")

# ---------------------------------------------------------------------------
# 2_dummy
# ---------------------------------------------------------------------------
w2 = wb.create_sheet("2_dummy")
for col, larg in zip("ABCDE", (24, 12, 18, 18, 18)):
    w2.column_dimensions[col].width = larg
w2["A1"] = "Regressor binário: o prêmio do diploma"
w2["A1"].font = TIT
cabecalho(w2, 3, ["Nível", "n", "Salário-hora médio", "Mediana (R$)", "Média de lsal"])
niveis = ["Fund. incompleto", "Fundamental", "Médio", "Superior"]
NIV, SAL, LS = X("C"), X("G"), X("S")
for k, nv in enumerate(niveis, start=4):
    w2.cell(k, 1, nv).font = TX
    w2.cell(k, 2, f'=COUNTIF({NIV},A{k})').number_format = "0"
    w2.cell(k, 3, f'=AVERAGEIF({NIV},A{k},{SAL})').number_format = '"R$" #,##0.00'
    w2.cell(k, 4, f'=MEDIAN(IF({NIV}=A{k},{SAL}))')
    w2[f"D{k}"] = ArrayFormula(f"D{k}", f'=MEDIAN(IF({NIV}=A{k},{SAL}))')
    w2[f"D{k}"].number_format = '"R$" #,##0.00'
    w2.cell(k, 5, f'=AVERAGEIF({NIV},A{k},{LS})').number_format = "0.0000"
    for j in range(1, 6):
        w2.cell(k, j).border = BORDA
        w2.cell(k, j).font = TX

w2.column_dimensions["A"].width = 46
w2["A10"] = "Superior × médio"
w2["A10"].font = B
bloco(w2, 11, "Prêmio na média aritmética", "=C7/C6-1", "0.0%",
      "É o número que aparece em relatórios como o da OCDE.", destaque=True)
bloco(w2, 12, "Prêmio na mediana", "=D7/D6-1", "0.0%")
bloco(w2, 13, "Diferença de médias de lsal", "=E7-E6", "0.0000",
      "É o β̂₁ de lsal = β₀ + β₁·superior, estimado só com médio e superior.")
bloco(w2, 14, "Prêmio na média geométrica = e^dif − 1", "=EXP(B13)-1", "0.0%",
      "Menor que o prêmio aritmético: a média geométrica pesa menos os salários muito altos.")
w2["A16"] = ("Lição: numa regressão com uma única dummy, o intercepto é a média do grupo base e o "
             "coeficiente é a diferença de médias. Ainda não é efeito causal do diploma.")
w2["A16"].font = NOTA
w2.merge_cells("A16:E17")
w2["A16"].alignment = WRAP

# ---------------------------------------------------------------------------
# 3_multipla — PROJ.LIN (LINEST) com estatísticas
# ---------------------------------------------------------------------------
w3 = wb.create_sheet("3_multipla")
w3.column_dimensions["A"].width = 26
for j in range(2, 15):
    w3.column_dimensions[get_column_letter(j)].width = 12
w3["A1"] = "Regressão múltipla com PROJ.LIN (LINEST)"
w3["A1"].font = TIT
w3["A2"] = ("PROJ.LIN devolve os coeficientes em ORDEM INVERSA à das colunas de X, com o intercepto por último. "
            "Linha 1: coeficientes · linha 2: erros-padrão clássicos · linha 3: R² e σ̂ · "
            "linha 4: F e graus de liberdade · linha 5: SQE e SQR.")
w3["A2"].font = NOTA
w3["A2"].alignment = WRAP
w3.merge_cells("A2:M3")
w3.row_dimensions[2].height = 30

nomes_x = ["educ", "exper", "exper2", "mulher", "norte", "nordeste", "sul",
           "centro_oeste", "urbano"]
modelos = [
    ("(M1) educ, exper, exper², mulher", "J", "M", nomes_x[:4]),
    ("(M2) + região e urbano", "J", "R", nomes_x),
    ("(M3) + superior", None, None, nomes_x + ["superior"]),
    ("(M4) + habilidade", None, None, nomes_x + ["superior", "habilidade"]),
]
# M3 e M4 precisam de colunas vizinhas: J..R + T (+U). S (lsal) fica no meio,
# então usamos uma cópia das colunas em uma área auxiliar da aba.
aux = wb.create_sheet("aux_X")
aux["A1"] = "Cópia de J:R, T e U de 'dados' lado a lado (usada pelos modelos M3 e M4)."
aux["A1"].font = NOTA
for j, (nome, origem) in enumerate(
        list(zip(nomes_x, "JKLMNOPQR")) + [("superior", "T"), ("habilidade", "U")], start=1):
    c = aux.cell(2, j, nome)
    c.font = H
    c.fill = FILL_H
    for i in range(2, U + 1):
        aux.cell(i + 1, j, f"=dados!{origem}{i}")
AUXU = U + 1

def linest(w, ini, titulo, faixa_x, nomes):
    k = len(nomes)
    w.cell(ini, 1, titulo).font = B
    rot = list(reversed(nomes)) + ["const"]
    for j, nm in enumerate(rot, start=2):
        c = w.cell(ini + 1, j, nm)
        c.font = H
        c.fill = FILL_H
        c.alignment = Alignment(horizontal="center")
    for i, t in enumerate(["coeficiente", "erro-padrão", "R² | σ̂", "F | gl", "SQE | SQR"]):
        w.cell(ini + 2 + i, 1, t).font = TX
    ref = f"B{ini+2}:{get_column_letter(k+2)}{ini+6}"
    w[f"B{ini+2}"] = ArrayFormula(ref, f"=IFERROR(LINEST({Y_L},{faixa_x},TRUE,TRUE),\"\")")
    for rr in range(ini + 2, ini + 7):
        for cc in range(2, k + 3):
            cel = w.cell(rr, cc)
            cel.number_format = "0.00000"
            cel.border = BORDA
            cel.font = TX
            if rr == ini + 2:
                cel.fill = FILL_R
                cel.font = B
    # destaca educ
    col_educ = get_column_letter(2 + rot.index("educ"))
    w[f"{col_educ}{ini+2}"].fill = FILL_K
    return col_educ, rot

lin = 5
pos = {}
for titulo, c0, c1, nomes in modelos:
    if c0:
        faixa = f"dados!${c0}$2:${c1}${U}"
    else:
        faixa = f"aux_X!$A$3:${get_column_letter(len(nomes))}${AUXU}"
    pos[titulo[:4]] = (lin, *linest(w3, lin, titulo, faixa, nomes))
    lin += 9

# Viés de variável omitida com fórmulas
l3, ce3, rot3 = pos["(M3)"]
l4, ce4, rot4 = pos["(M4)"]
col_hab = get_column_letter(2 + rot4.index("habilidade"))
w3.cell(lin, 1, "Viés de variável omitida").font = TIT
lin += 1
# delta: regressão auxiliar habilidade ~ educ + controles (mesmos de M3)
w3.cell(lin, 1, "Regressão auxiliar: habilidade em educ e nos controles de M3 (só a 1ª linha)").font = NOTA
k3 = len(rot3) - 1
for j, nm in enumerate(rot3, start=2):
    c = w3.cell(lin + 1, j, nm)
    c.font = H
    c.fill = FILL_H
ref = f"B{lin+2}:{get_column_letter(k3+2)}{lin+2}"
w3[f"B{lin+2}"] = ArrayFormula(
    ref, f"=LINEST(aux_X!$K$3:$K${AUXU},aux_X!$A$3:${get_column_letter(k3)}${AUXU},TRUE,FALSE)")
for cc in range(2, k3 + 3):
    w3.cell(lin + 2, cc).number_format = "0.00000"
w3.cell(lin + 2, 1, "coeficiente").font = TX
la = lin + 2
lin += 4
bloco(w3, lin, "β̂ curto: educ em M3", f"={ce3}{l3+2}")
bloco(w3, lin + 1, "β̂ longo: educ em M4", f"={ce4}{l4+2}")
bloco(w3, lin + 2, "γ̂: habilidade em M4", f"={col_hab}{l4+2}")
bloco(w3, lin + 3, "δ̂: educ na regressão auxiliar", f"={ce3}{la}")
bloco(w3, lin + 4, "β̂ longo + γ̂·δ̂", f"=B{lin+1}+B{lin+2}*B{lin+3}", "0.0000",
      "Reproduz exatamente o β̂ curto: o viés é γ̂·δ̂ > 0.", destaque=True)
bloco(w3, lin + 5, "Viés em % do β̂ longo", f"=B{lin}/B{lin+1}-1", "0.0%")

# Efeito marginal da experiência (M3)
lin += 7
ce_exp = get_column_letter(2 + rot3.index("exper"))
ce_exp2 = get_column_letter(2 + rot3.index("exper2"))
w3.cell(lin, 1, "Experiência (modelo M3)").font = TIT
bloco(w3, lin + 1, "Anos de experiência", 10, "0", "Altere este valor.")
w3[f"B{lin+1}"].font = Font(name=F, size=11, color="0000FF")
w3[f"B{lin+1}"].fill = PatternFill("solid", fgColor="FFFF00")
bloco(w3, lin + 2, "Efeito marginal = β̂exper + 2·β̂exper²·x",
      f"={ce_exp}{l3+2}+2*{ce_exp2}{l3+2}*B{lin+1}", "0.0000")
bloco(w3, lin + 3, "Experiência do salário máximo", f"=-{ce_exp}{l3+2}/(2*{ce_exp2}{l3+2})", "0.0")

wb.move_sheet("aux_X", offset=1)
out = BASE / "dados" / "laboratorio_excel.xlsx"
wb.save(out)
print(out)
