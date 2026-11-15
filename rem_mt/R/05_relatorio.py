"""
05_relatorio.py — gera resultados/Resultados_DDD_REM_MT.docx a partir das
tabelas e figuras produzidas pelos scripts R (03 e 04).
Execute a partir da pasta rem_mt/:  python3 R/05_relatorio.py
"""
import os
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

T = "resultados/tabelas/"
F = "resultados/figuras/"
painel = pd.read_csv("dados/painel_rem_mt.csv")
p = painel[painel.uf != "TO"]


def br(x, d=3):
    """número no formato brasileiro"""
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def stars(pv):
    return "***" if pv < .01 else "**" if pv < .05 else "*" if pv < .1 else ""


doc = Document()
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(11)
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.5)


def tabela(df, titulo=None, nota=None, larg=None):
    if titulo:
        par = doc.add_paragraph()
        r = par.add_run(titulo)
        r.bold = True
        r.font.size = Pt(10)
    t = doc.add_table(rows=1, cols=len(df.columns))
    t.style = "Light Grid Accent 1"
    for j, c in enumerate(df.columns):
        t.rows[0].cells[j].text = str(c)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = str(v)
    for row in t.rows:
        for c in row.cells:
            for pp in c.paragraphs:
                for r in pp.runs:
                    r.font.size = Pt(9)
    if nota:
        n = doc.add_paragraph()
        rn = n.add_run(nota)
        rn.italic = True
        rn.font.size = Pt(8.5)
    doc.add_paragraph()


def figura(arq, legenda, largura=15.5):
    doc.add_picture(F + arq, width=Cm(largura))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = doc.add_paragraph()
    r = c.add_run(legenda)
    r.italic = True
    r.font.size = Pt(9)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER


def limpa_etable(arq):
    """transforma a saída do etable (fixest) em tabela legível"""
    d = pd.read_csv(arq).drop(columns="rn").fillna("")
    d.columns = [""] + d.iloc[0, 1:].tolist()
    d = d.iloc[1:]
    rot = {"Dependent Var.:": "Variável dependente", "mt x pos": "MT × Pós",
           "ddd": "MT × Alto × Pós", "ddd x bioma = Amazonia": "MT × Alto × Pós × Amazônia",
           "ddd x bioma = Cerrado": "MT × Alto × Pós × Cerrado", "id": "EF município-bioma",
           "bioma-ano": "EF bioma × ano", "uf-bioma-ano": "EF estado × bioma × ano",
           "alto-bioma-ano": "EF faixa de risco × bioma × ano", "Family": "Estimador",
           "S.E.: Clustered": "Cluster", "Observations": "Observações"}
    d = d[d.iloc[:, 0].isin(rot.keys()) | (d.iloc[:, 0] == "R2")]
    d.iloc[:, 0] = d.iloc[:, 0].map(lambda x: rot.get(x, x))
    d = d.replace({"Yes": "Sim", "No": "Não", "by: cod_ibge": "município"})
    obs = d.iloc[:, 0] == "Observações"
    d.loc[obs] = d.loc[obs].apply(lambda c: c.str.replace(",", "."))
    d.loc[~obs] = d.loc[~obs].apply(lambda c: c.str.replace(".", ",", regex=False)
                                    .str.replace(r",(?=\s|$)", ".", regex=True))
    return d.reset_index(drop=True)


# ------------------------------------------------------------------ dados
rob = pd.read_csv(T + "tab5_robustez.csv")
princ = rob.iloc[0]
b, ep, pv = princ.beta, princ.ep, princ.p
es = pd.read_csv(T + "tab3_estudo_eventos.csv")
esb = pd.read_csv(T + "tab3b_estudo_eventos_bioma.csv")
bio = pd.read_csv(T + "tab4_biomas.csv")
inf = pd.read_csv(T + "tab7_inferencia.csv")
perm = pd.read_csv(T + "tab7a_permutacao_estados.csv")
vaz = pd.read_csv(T + "tab6_vazamento.csv").iloc[0]
cel = pd.read_csv(T + "tab1_celulas_ddd.csv")
mt_al = pd.read_csv(T + "tab9_mt_amazonia_legal_linha_base.csv")
co2 = pd.read_csv(T + "tab10b_co2_por_bioma.csv")
cmp = pd.read_csv(T + "tab10_co2_comparacoes.csv")
anual = pd.read_csv(T + "tab10c_area_evitada_anual.csv")
hon = pd.read_csv(T + "tab8_honestdid.csv") if os.path.exists(T + "tab8_honestdid.csv") else None
media_pre = p[(p.mt == 1) & (p.alto == 1) & (p.pos == 0)].y.mean()


# ------------------------------------------------------------------ título
h = doc.add_heading("Efeito do Programa REM MT sobre o desmatamento: "
                    "resultados da estimação por triplas diferenças", 0)
doc.add_paragraph("Relatório de resultados — versão preliminar (dados PRODES até 2024). "
                  "Código e dados em rem_mt/ (scripts R/01 a R/05).").runs[0].italic = True

# ------------------------------------------------------------------ síntese
doc.add_heading("1. Síntese", 1)
pts = [
    f"Na especificação principal, o desmatamento anual nos municípios de alto risco de MT caiu "
    f"{br(abs(b), 3)} ponto percentual da área municipal por ano depois de 2018, além do que caiu "
    f"nos municípios de baixo risco de MT e descontada a mesma diferença nos estados de controle "
    f"(EP agrupado por município = {br(ep, 3)}; p = {br(pv, 3)}). Sobre a média pré-programa do grupo "
    f"tratado ({br(media_pre, 3)}% da área/ano), isso equivale a uma redução de cerca de "
    f"{br(100*abs(b)/media_pre, 0)}%.",
    "O efeito não é estável no tempo: aparece em 2021 e 2022 e volta a zero em 2023–2024. "
    "Os anos de 2018 a 2020 não mostram efeito.",
    "A hipótese de identificação é frágil. O teste conjunto de pré-tendências rejeita a "
    "igualdade a zero dos coeficientes de 2010–2016, e os coeficientes de 2015–2016 são positivos — "
    "sinal de volta à média, sobretudo no Cerrado.",
    "Com a inferência adequada a um único estado tratado, o efeito deixa de ser significativo: "
    "MT fica em 4.º lugar entre 6 estados na permutação, e o intervalo à la Conley–Taber inclui zero.",
    "Conclusão: os dados são compatíveis com um efeito do REM MT nos municípios de alto risco em "
    "2021–2022, mas não permitem afirmar, com a confiança usual, que o programa reduziu o "
    "desmatamento além da tendência no conjunto do período 2018–2024 (H1 não confirmada com "
    "inferência robusta).",
]
for t in pts:
    doc.add_paragraph(t, style="List Bullet")

# ------------------------------------------------------------------ dados
doc.add_heading("2. Dados e amostra efetivamente usados", 1)
doc.add_paragraph(
    "Resultado: desmatamento anual PRODES/INPE por município (painel TerraBrasilis, malha municipal "
    "atual, o que dispensa a reagregação em AMC), dividido pela área territorial do município "
    "(IBGE 2022) e expresso em % da área. O ano PRODES t vai de agosto de t−1 a julho de t. "
    "Risco: desmatamento médio anual 2012–2016 em % da área; alto risco = tercil superior dentro "
    "de cada estado × bioma. Unidade: porção do município em cada bioma.")
amostra = (p.groupby(["bioma", "uf"])
           .agg(unidades=("id", "nunique"),
                alto_risco=("id", lambda s: s[p.loc[s.index, "alto"] == 1].nunique()),
                anos=("ano", lambda s: f"{s.min()}–{s.max()}"))
           .reset_index())
amostra["papel"] = amostra.uf.map(lambda u: "Tratado" if u == "MT" else "Controle")
tabela(amostra[["bioma", "uf", "papel", "unidades", "alto_risco", "anos"]],
       "Tabela 1 — Amostra principal (município × bioma)",
       f"Total: {p.id.nunique()} unidades e {len(p):,} observações. Tocantins entra apenas na robustez; "
       "Acre e Pantanal excluídos. O PRODES Cerrado só é anual a partir de 2013.".replace(",", "."))

c2 = cel.copy()
for c in ["antes", "depois", "dif"]:
    c2[c] = c2[c].map(lambda x: br(x, 3))
c2.columns = ["Grupo", "Risco", "Antes de 2018", "Depois de 2018", "Diferença"]
dd_mao = (cel.dif[0] - cel.dif[1]) - (cel.dif[2] - cel.dif[3])
tabela(c2, "Tabela 2 — Médias das oito células (% da área municipal desmatada por ano)",
       f"DDD com médias simples = {br(dd_mao, 4)} p.p. Sem efeitos fixos e com painel desbalanceado "
       "entre biomas, este número é só ilustrativo; o estimador de referência é a regressão da Tabela 3.")

# ------------------------------------------------------------------ principal
doc.add_heading("3. Resultado principal (H1)", 1)
doc.add_paragraph(
    "Modelo: y_ist = β(MT × Alto × Pós) + α_i + δ_(estado×bioma×ano) + λ_(faixa de risco×bioma×ano) + ε. "
    "Os efeitos fixos de estado × bioma × ano absorvem qualquer choque comum a MT (inclusive o efeito "
    "médio do REM sobre todo o estado); β mede o efeito diferencial nos municípios de alto risco.")
t2 = limpa_etable(T + "tab2_principal.csv")
tabela(t2, "Tabela 3 — DiD simples e triplas diferenças",
       "Erros-padrão agrupados por município entre parênteses. *** p<0,01; ** p<0,05; * p<0,1; "
       ". p<0,1 na notação do fixest. DiD simples: só municípios de alto risco, MT × controles, "
       "efeitos fixos de município e bioma × ano. PPML usa a área desmatada em km²; o coeficiente é "
       "semi-elasticidade (exp(β)−1 ≈ variação %).")
doc.add_paragraph(
    f"Leitura: β = {br(b, 4)} significa que, depois de 2018, os municípios de alto risco de MT "
    f"desmataram {br(abs(b), 3)} p.p. da sua área a menos por ano do que o esperado. As versões "
    "em asinh(km²) e PPML têm o mesmo sinal, mas são menos precisas (p > 0,05), o que indica que o "
    "resultado em taxa depende em parte de municípios grandes em área.")

# ------------------------------------------------------------------ eventos
doc.add_heading("4. Dinâmica do efeito e pré-tendências (H2)", 1)
figura("fig1_estudo_eventos.png",
       "Figura 1 — Estudo de eventos (β_k, IC 95%, ano-base 2017). Amostra conjunta.")
figura("fig1b_estudo_eventos_bioma.png",
       "Figura 2 — Estudo de eventos por bioma. O Cerrado só tem PRODES anual desde 2013.")
pos = es[es.ano >= 2018]
doc.add_paragraph(
    "Pós-programa: os coeficientes são próximos de zero em 2018–2020, negativos e significativos "
    f"em 2021 ({br(pos[pos.ano==2021].Estimate.iloc[0],3)}) e 2022 ({br(pos[pos.ano==2022].Estimate.iloc[0],3)}), "
    "e voltam para perto de zero em 2023–2024. H2 (efeito crescente a partir de 2019) é confirmada "
    "apenas parcialmente: o efeito surge com atraso e não persiste.")
doc.add_paragraph(
    "Pré-programa: o teste conjunto de que β_2010…β_2016 = 0 é rejeitado (F = 3,19; p = 0,002). "
    "Há dois problemas: (i) 2010 é bem negativo, o que reflete a Amazônia no fim da queda pós-PPCDAm; "
    "(ii) 2015–2016 são positivos, ou seja, os municípios de alto risco de MT desmataram relativamente "
    "mais logo antes do programa. Parte da queda pós-2018 pode ser volta à média — exatamente a "
    "ameaça apontada no projeto. No Cerrado, os coeficientes de 2015 (0,18) e 2016 (0,27) são grandes, "
    "e o efeito médio do Cerrado deve ser lido com esse viés em mente.")

# ------------------------------------------------------------------ biomas
doc.add_heading("5. Heterogeneidade por bioma (H3)", 1)
tb = limpa_etable(T + "tab4_biomas.csv")
tabela(tb, "Tabela 4 — DDD por bioma")
doc.add_paragraph(
    "Contrário a H3, o coeficiente médio é maior e significativo no Cerrado e não significativo na "
    "Amazônia. Mas o estudo de eventos mostra que a Amazônia concentra o efeito de 2021–2022 "
    "(−0,22 e −0,17, ambos significativos), enquanto no Cerrado o coeficiente médio é inflado pelo "
    "pico de 2015–2016 (pré-tendência). A leitura mais cuidadosa é: efeito transitório na Amazônia "
    "em 2021–2022; evidência fraca no Cerrado.")

# ------------------------------------------------------------------ robustez
doc.add_heading("6. Robustez", 1)
r2 = rob.copy()
r2["β (EP)"] = [f"{br(x,4)}{stars(pp)} ({br(e,4)})" for x, e, pp in zip(r2.beta, r2.ep, r2.p)]
r2["p"] = r2.p.map(lambda x: br(x, 3))
r2["N"] = r2.n.map(lambda x: f"{x:,}".replace(",", "."))
r2 = r2.rename(columns={"especificacao": "Especificação"})[["Especificação", "β (EP)", "p", "N"]]
tabela(r2, "Tabela 5 — Testes de robustez (resultado: % da área desmatada/ano)",
       "EP agrupados por município. Risco contínuo: coeficiente por 1 desvio-padrão de risco.")
doc.add_paragraph(
    "O sinal negativo se mantém em quase todas as variações (cortes de risco, risco medido em "
    "2010–2014, retirada de cada estado de controle, exclusão dos controles a menos de 100 km de MT, "
    "fim em 2023). Com Tocantins no controle o efeito cai a −0,026 e perde significância. "
    "Com tendência linear própria para MT × alto risco o efeito fica maior (−0,11), o que é coerente "
    "com a pré-tendência positiva de 2013–2016. O placebo de data (programa fictício em 2014, dados "
    "2010–2017) dá +0,047, não significativo — sem efeito espúrio negativo antes do programa.")
doc.add_paragraph(
    f"Vazamento: nos municípios de controle de alto risco a menos de 100 km de MT o desmatamento "
    f"não subiu depois de 2018 em relação aos demais controles (β = {br(vaz.beta,3)}; p = {br(vaz.p,2)}). "
    "Não há sinal de deslocamento do desmatamento para os vizinhos, e por isso v = 0 na conversão em CO2.")

# ------------------------------------------------------------------ inferência
doc.add_heading("7. Inferência com um único estado tratado", 1)
i2 = inf.copy()
i2.columns = ["Método", "Resultado"]
tabela(i2, "Tabela 6 — Inferência")
pp_ = perm.copy()
pp_["beta"] = pp_.beta.map(lambda x: br(x, 4))
pp_.columns = ["Estado como 'tratado'", "β"]
tabela(pp_, "Tabela 7 — Permutação entre estados")
figura("fig2_permutacao.png",
       "Figura 3 — β de MT (vermelho) contra placebos em que RGIs dos estados de controle "
       "fazem o papel de MT, e contra os estados de controle (azul).")
doc.add_paragraph(
    "O erro-padrão agrupado por município supõe que os choques são independentes entre municípios, "
    "o que não vale quando o tratamento é um único estado. Na permutação entre estados, três dos "
    "cinco estados de controle têm |β| igual ou maior que o de MT (p = 0,67). Observação técnica: "
    "como os efeitos fixos de faixa de risco × bioma × ano são estimados com os próprios controles, os "
    "placebos de GO e MS são simétricos (o Cerrado só tem dois controles); com tão poucas posições, "
    "essa permutação tem baixo poder. A permutação entre regiões geográficas imediatas, que gera 500 "
    "falsos tratados de tamanho comparável a MT, dá p = 0,08, e o intervalo à la Conley–Taber vai de "
    "−0,168 a +0,008. Conclusão: evidência sugestiva, não conclusiva, ao nível de 5%.")

if hon is not None:
    doc.add_heading("8. Sensibilidade a desvios de tendências paralelas (HonestDiD)", 1)
    h2 = hon.copy()
    h2["Mbar"] = h2.Mbar.map(lambda x: "—" if pd.isna(x) else br(x, 1))
    h2["lb"] = h2.lb.map(lambda x: br(x, 3))
    h2["ub"] = h2.ub.map(lambda x: br(x, 3))
    h2.columns = ["M̄", "Limite inferior", "Limite superior", "Método"]
    tabela(h2, "Tabela 8 — IC robusto para o efeito médio 2018–2024 (Rambachan e Roth, 2023)",
           "Magnitudes relativas: o desvio de tendência pós-2018 pode ser até M̄ vezes o maior "
           "desvio observado entre anos consecutivos antes de 2018.")
    doc.add_paragraph(
        "Se o intervalo inclui zero já com M̄ pequeno, o resultado não tolera violações de "
        "tendência do tamanho das já observadas no pré-período — o que é o caso aqui, dado o salto "
        "entre 2016 e 2017 no estudo de eventos.")
    secao = 9
else:
    secao = 8

# ------------------------------------------------------------------ CO2
doc.add_heading(f"{secao}. Conversão em tCO2e e adicionalidade (H5)", 1)
doc.add_paragraph(
    "Área evitada = −β/100 × área municipal dos municípios de alto risco de MT × 7 anos (2018–2024), "
    "por bioma. Emissões = área × fator de emissão × (1 − v)(1 − r), com v = 0 (sem vazamento detectado) "
    "e r = 10% (reserva de não permanência). Fatores de emissão PROVISÓRIOS: 550 tCO2e/ha (Amazônia) e "
    "200 tCO2e/ha (Cerrado) — devem ser substituídos pelos valores do FREL/Inventário Nacional.")
c3 = co2.copy()
c3 = pd.DataFrame({
    "Bioma": c3.bioma,
    "β": c3.beta.map(lambda x: br(x, 4)),
    "Área mun. alto risco (km²)": c3.area_mun_km2.map(lambda x: br(x, 0)),
    "ha evitados [IC95]": [f"{br(a,0)} [{br(l,0)}; {br(u,0)}]" for a, l, u in zip(c3.ha_evitados, c3.ha_li, c3.ha_ls)],
    "tCO2e [IC95]": [f"{br(a/1e6,1)} mi [{br(l/1e6,1)}; {br(u/1e6,1)}]" for a, l, u in zip(c3.tco2e, c3.tco2e_li, c3.tco2e_ls)],
})
tabela(c3, "Tabela 9 — Área e emissões evitadas, 2018–2024 (alto risco de MT)")
cm = cmp.copy()
cm.columns = ["Referência", "Valor"]
tabela(cm, "Tabela 10 — Três comparações do projeto")
figura("fig3_mt_linha_base.png",
       "Figura 4 — MT (PRODES Amazônia Legal): desmatamento, gatilho do REM e linha de base histórica.")
doc.add_paragraph(
    "(a) Meta da fase 1: a estimativa pontual (≈ 64 milhões tCO2e) supera a meta de 10,1 milhões, mas "
    "o intervalo de confiança vai de valores negativos a quase 180 milhões, porque o efeito na Amazônia "
    "não é significativo. Com a incerteza atual, não é possível afirmar nem negar que as reduções "
    "remuneradas foram adicionais (H5 inconclusiva). (b) Os 160 mil ha divulgados pelo programa para "
    "2021–2022 ficam dentro do intervalo do DDD para esses anos (≈ 16 mil a 230 mil ha; ponto ≈ 123 mil ha). "
    "(c) Pela linha de base histórica (média 2013–2017 = 1.311 km²), MT quase não teria reduções a "
    "creditar em 2018–2024: o desmatamento subiu em 2019–2023 e superou o gatilho de 1.788 km² em cinco "
    "anos. Ou seja, a linha de base histórica e o contrafactual causal divergem no sentido oposto ao "
    "usual: o DDD sugere que, sem o programa, o aumento de 2019–2022 nos municípios de alto risco teria "
    "sido maior do que foi.")
doc.add_paragraph(
    "Gatilho de desempenho: o desmatamento de MT não se concentra logo abaixo de 1.788 km² — os anos "
    "abaixo do gatilho ficam entre 770 e 1.500 km² (2009–2018) ou em 1.302 km² (2024), e entre 2019 e "
    "2023 o estado ficou acima. Não há sinal de esforço calibrado ao limite.")

# ------------------------------------------------------------------ hipóteses
doc.add_heading(f"{secao+1}. Quadro-resumo das hipóteses", 1)
hip = pd.DataFrame({
    "Hipótese": ["H1: β < 0 no alto risco de MT após 2018", "H2: efeito crescente a partir de 2019",
                 "H3: maior na Amazônia", "H4: fiscalização como canal",
                 "H5: tCO2e do DDD < remuneradas"],
    "Resultado": ["β = −0,080 (p = 0,035 com EP por município); não significativo com permutação "
                  "(p = 0,08 por RGI; 0,67 por estado)",
                  "Parcial: efeito só em 2021–2022, some em 2023–2024",
                  "Efeito médio maior no Cerrado, mas com pré-tendência; efeito de 2021–2022 concentrado "
                  "na Amazônia",
                  "Não testada: autuações da SEMA-MT por município exigem pedido por LAI",
                  "Inconclusiva: IC das emissões evitadas contém a meta e o zero"],
})
tabela(hip, "Tabela 11 — Hipóteses do projeto")

# ------------------------------------------------------------------ limitações
doc.add_heading(f"{secao+2}. Limitações e próximos passos", 1)
for t in [
    "Trocar o denominador (área municipal) pela floresta remanescente de 2008, a partir dos mapas PRODES.",
    "Repetir com MapBiomas, que tem a mesma série anual nos dois biomas e cobre 2010–2012 no Cerrado.",
    "Obter por LAI as autuações e embargos da SEMA-MT e os desembolsos do REM por município, para "
    "testar H4 e a extensão por dose.",
    "Investigar a pré-tendência de 2015–2016: controlar choques específicos dos municípios de alto risco "
    "de MT (lista de prioritários do MMA, operações, embargos) e testar especificações com tendências "
    "por grupo.",
    "Substituir os fatores de emissão provisórios pelos do FREL e propagar a incerteza de β por todos "
    "os anos (covariância do estudo de eventos).",
    "Distância até MT medida entre sedes e localidades (proxy da distância à divisa); refinar com a "
    "malha municipal em SIG.",
]:
    doc.add_paragraph(t, style="List Bullet")

out = "resultados/Resultados_DDD_REM_MT.docx"
doc.save(out)
print("Relatório salvo em", out)
