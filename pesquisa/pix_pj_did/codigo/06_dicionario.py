"""
06 - Gera o dicionário de variáveis do painel (dados/dicionario_variaveis.csv).
Execute de dentro de codigo/:  python 06_dicionario.py
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BCB_PIX, RF, ESTBAN = "BCB - Estatísticas do Pix", "Receita Federal - CNPJ (set/2024)", "BCB - ESTBAN"
IBGE, CONSTR = "IBGE", "Construída"
D = {
    "cod_ibge": ("Código IBGE do município (7 dígitos)", IBGE, "identificador"),
    "id": ("Identificador numérico para o pacote did (= cod_ibge)", CONSTR, "identificador"),
    "municipio": ("Nome do município", BCB_PIX, "identificador"),
    "uf": ("Unidade da Federação (MT, MS, GO)", IBGE, "identificador"),
    "anomes": ("Ano e mês (AAAAMM)", CONSTR, "tempo"),
    "ano": ("Ano", CONSTR, "tempo"), "mes": ("Mês", CONSTR, "tempo"),
    "periodo": ("Índice do mês: 1 = jan/2019 ... 72 = dez/2024", CONSTR, "tempo"),
    "qt_pix_pj": ("Transações Pix com PJ (pagadora + recebedora) no mês; 0 antes de nov/2020", BCB_PIX, "Pix"),
    "vl_pix_pj": ("Valor (R$) das transações Pix com PJ (pagadora + recebedora)", BCB_PIX, "Pix"),
    "qt_pix_total": ("Total de transações Pix pagas por PF e PJ do município", BCB_PIX, "Pix"),
    "qt_pagadorpj": ("Transações Pix em que a PJ do município paga", BCB_PIX, "Pix"),
    "qt_recebedorpj": ("Transações Pix em que a PJ do município recebe", BCB_PIX, "Pix"),
    "vl_recebedorpj": ("Valor (R$) recebido via Pix por PJ do município", BCB_PIX, "Pix"),
    "qt_pes_recebedorpj": ("Nº de PJ distintas que receberam Pix no mês", BCB_PIX, "Pix"),
    "qt_pes_pagadorpj": ("Nº de PJ distintas que pagaram Pix no mês", BCB_PIX, "Pix"),
    "ativas": ("Estabelecimentos (CNPJ) ativos no fim do mês (reconstruído)", RF, "empresas"),
    "ativas_matriz": ("Estabelecimentos-matriz ativos no fim do mês", RF, "empresas"),
    "ativas_mei": ("Estabelecimentos ativos optantes pelo MEI no fim do mês", RF, "empresas"),
    "ativas_simples": ("Estabelecimentos ativos optantes pelo Simples Nacional", RF, "empresas"),
    "ativas_pequenos": ("Estabelecimentos ativos de ME, EPP ou MEI (porte atual)", RF, "empresas"),
    "aberturas_cnpj": ("CNPJs (estabelecimentos) abertos no mês", RF, "empresas"),
    "aberturas_matriz": ("Matrizes abertas no mês", RF, "empresas"),
    "aberturas_mei": ("Novos MEIs: CNPJ aberto no mês com opção pelo MEI no mesmo mês", RF, "empresas"),
    "opcoes_mei": ("Opções pelo MEI no mês (inclui empresas já existentes)", RF, "empresas"),
    "aberturas_pequenos": ("Aberturas de ME, EPP ou MEI no mês", RF, "empresas"),
    "baixas_cnpj": ("Estabelecimentos baixados no mês (situação 08)", RF, "empresas"),
    "credito_total": ("Operações de crédito, verbete 160 (R$; PF + PJ, só bancos)", ESTBAN, "crédito"),
    "emprestimos": ("Empréstimos e títulos descontados, verbete 161 (R$)", ESTBAN, "crédito"),
    "financiamentos": ("Financiamentos, verbete 162 (R$)", ESTBAN, "crédito"),
    "credito_rural": ("Financiamentos rurais, verbete 163 (R$)", ESTBAN, "crédito"),
    "fin_agroind": ("Financiamentos agroindustriais, verbete 167 (R$; só a partir de jul/2022)", ESTBAN, "crédito"),
    "dep_vista": ("Depósitos à vista, verbetes 401-419 agrupados (R$)", ESTBAN, "crédito"),
    "dep_poupanca": ("Depósitos de poupança, verbete 420 (R$)", ESTBAN, "crédito"),
    "dep_prazo": ("Depósitos a prazo, verbete 432 (R$)", ESTBAN, "crédito"),
    "n_agencias": ("Nº de agências bancárias (AGEN_PROCESSADAS)", ESTBAN, "crédito"),
    "n_instituicoes": ("Nº de bancos com crédito > 0 no município", ESTBAN, "crédito"),
    "ihh_credito": ("Herfindahl-Hirschman do crédito entre bancos (0-1)", ESTBAN, "crédito"),
    "ihh_deposito": ("Herfindahl-Hirschman dos depósitos à vista entre bancos (0-1)", ESTBAN, "crédito"),
    "estban_imputado": ("1 = algum banco em não-reporte teve saldo imputado (LOCF)", ESTBAN, "crédito"),
    "tem_agencia_estban": ("1 = município aparece no ESTBAN (tem agência bancária)", ESTBAN, "crédito"),
    "pop": ("População (estimativas IBGE; Censo 2022; 2023 interpolado)", IBGE, "covariável"),
    "pib_pc": ("PIB per capita (R$ correntes; 2024 = 2023)", IBGE, "covariável"),
    "pop_2019": ("População em 2019", IBGE, "covariável pré-tratamento"),
    "ln_pop_2019": ("ln(população 2019)", IBGE, "covariável pré-tratamento"),
    "ln_pib_pc_2019": ("ln(PIB per capita 2019)", IBGE, "covariável pré-tratamento"),
    "idhm_2010": ("IDHM 2010 (Atlas Brasil, via Ipeadata)", "PNUD/IPEA/FJP", "covariável pré-tratamento"),
    "n_estab_ensino_superior_2019": ("Estabelecimentos ativos com CNAE de educação superior, dez/2019", RF, "covariável pré-tratamento"),
    "campus": ("1 = há estabelecimento de educação superior (dez/2019)", RF, "covariável pré-tratamento"),
    "pct_simples_2019": ("% de estabelecimentos ativos no Simples Nacional, dez/2019", RF, "covariável pré-tratamento"),
    "pct_mei_2019": ("% de estabelecimentos ativos que são MEI, dez/2019", RF, "covariável pré-tratamento"),
    "y1_pix_pj_por_empresa": ("Y1: transações Pix com PJ / estabelecimentos ativos (até set/2024)", CONSTR, "resultado"),
    "y1_pix_pj_mil_hab": ("Y1 alternativo: transações Pix com PJ por mil habitantes", CONSTR, "resultado"),
    "y1b_pix_pj_por_recebedora": ("Transações recebidas por PJ recebedora de Pix (margem intensiva)", CONSTR, "resultado"),
    "empresas_recebem_pix_mil_hab": ("PJ que recebem Pix por mil habitantes", CONSTR, "resultado"),
    "pct_empresas_recebem_pix": ("% dos estabelecimentos ativos que receberam Pix no mês", CONSTR, "resultado"),
    "y2_aberturas_mei": ("Y2: novos MEIs no mês (até set/2024)", CONSTR, "resultado"),
    "y3_ihh_credito": ("Y3: IHH do crédito bancário (proxy do IHH do crédito PJ)", CONSTR, "resultado"),
    "y5_credito_pc": ("Y5: crédito bancário total per capita (R$; proxy do crédito PJ)", CONSTR, "resultado"),
    "amostra_50a600mil": ("1 = população 2019 entre 50 mil e 600 mil (amostra do artigo, 40 municípios)", CONSTR, "amostra"),
}
for y in ["y1_pix_pj_mil_hab", "y5_credito_pc", "y1_pix_pj_por_empresa", "y2_aberturas_mei"]:
    D["asinh_" + y] = (f"asinh({y})", CONSTR, "resultado")
G = {
    "primeira_pj": "1º mês com transação Pix envolvendo PJ (definição original do artigo)",
    "difusao25": "1º mês em que as PJ recebedoras de Pix atingem 25% do nível médio de 2024 do município",
    "difusao50": "idem, 50% do nível médio de 2024",
    "adesao10": "1º mês em que >= 10% dos estabelecimentos ativos recebem Pix",
    "adesao25": "1º mês em que >= 25% dos estabelecimentos ativos recebem Pix (RECOMENDADA)",
    "adesao50": "1º mês em que >= 50% dos estabelecimentos ativos recebem Pix (não atingido na amostra até set/2024)",
}
for k, txt in G.items():
    D[f"G_{k}"] = (f"Coorte (AAAAMM; 0 = nunca tratado): {txt}", CONSTR, "tratamento")
    D[f"G_{k}_t"] = (f"Coorte G_{k} no índice periodo (1-72; 0 = nunca tratado), para o did", CONSTR, "tratamento")
    D[f"D_{k}"] = (f"Tratamento: 1[anomes >= G_{k}]", CONSTR, "tratamento")

cols = pd.read_csv(RAIZ / "dados" / "painel_pix_pj_mensal.csv", nrows=0).columns
faltam = [c for c in cols if c not in D]
assert not faltam, f"sem descrição: {faltam}"
pd.DataFrame([(c, *D[c]) for c in cols],
             columns=["variavel", "descricao", "fonte", "grupo"]).to_csv(
    RAIZ / "dados" / "dicionario_variaveis.csv", index=False)
print(len(cols), "variáveis documentadas")
