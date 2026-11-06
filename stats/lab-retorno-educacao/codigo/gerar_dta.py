"""Converte as duas bases do Laboratório para o formato do Stata (.dta, versão 118).

Inclui as variáveis derivadas usadas nas aulas, rótulos de variáveis e rótulos
de valores. Uso:  python gerar_dta.py   (requer numpy e pandas)
"""
from pathlib import Path

import numpy as np
import pandas as pd

DADOS = Path(__file__).resolve().parents[1] / "dados"

# ---------------------------------------------------------------------------
# Exemplo 1: trabalhadores
# ---------------------------------------------------------------------------
df = pd.read_csv(DADOS / "pnad_simulada.csv")
df["lsal"] = np.log(df["salario_hora"])
df["exper2"] = df["exper"] ** 2
df["educ_mulher"] = df["educ"] * df["mulher"]
REG = ["Sudeste", "Norte", "Nordeste", "Sul", "Centro-Oeste"]
NIV = ["Fund. incompleto", "Fundamental", "Médio", "Superior"]
df["regiao"] = df["regiao"].map({r: i for i, r in enumerate(REG, start=1)}).astype("int8")
df["nivel"] = df["nivel"].map({r: i for i, r in enumerate(NIV, start=1)}).astype("int8")
SIMNAO = {0: "Não", 1: "Sim"}
vl1 = {"regiao": dict(enumerate(REG, start=1)), "nivel": dict(enumerate(NIV, start=1))}
vl1.update({c: SIMNAO for c in ["norte", "nordeste", "sul", "centro_oeste", "urbano", "mulher",
                                "fundamental", "medio", "superior"]})
rot1 = {
    "id": "Identificador do trabalhador",
    "regiao": "Região (1 = Sudeste, base)",
    "norte": "Mora no Norte",
    "nordeste": "Mora no Nordeste",
    "sul": "Mora no Sul",
    "centro_oeste": "Mora no Centro-Oeste",
    "urbano": "Mora em área urbana",
    "mulher": "Mulher",
    "idade": "Idade (anos)",
    "educ": "Anos de estudo",
    "nivel": "Nível de ensino (1 = fund. incompleto, base)",
    "fundamental": "Fundamental completo (maior nível)",
    "medio": "Médio completo (maior nível)",
    "superior": "Superior completo",
    "exper": "Experiência potencial (anos)",
    "educ_mae": "Anos de estudo da mãe",
    "horas": "Horas trabalhadas por semana",
    "salario_hora": "Salário por hora (R$)",
    "renda_mensal": "Renda mensal do trabalho (R$)",
    "habilidade": "Habilidade padronizada (não observada na vida real)",
    "lsal": "ln(salário por hora)",
    "exper2": "Experiência ao quadrado",
    "educ_mulher": "Interação educ x mulher",
}
df.to_stata(DADOS / "pnad_simulada.dta", write_index=False, version=118,
            variable_labels=rot1, value_labels=vl1,
            data_label="Laboratório Vale a pena estudar? Trabalhadores simulados (dados fictícios)")

# ---------------------------------------------------------------------------
# Exemplo 2: municípios e campus federal
# ---------------------------------------------------------------------------
dm = pd.read_csv(DADOS / "municipios_campus.csv")
dm["lrenda10"] = np.log(dm["renda_pc_2010"])
dm["lrenda00"] = np.log(dm["renda_pc_2000"])
dm["lpop"] = np.log(dm["pop_2000"])
dm["dlrenda"] = dm["lrenda10"] - dm["lrenda00"]
dm["dist100"] = dm["dist_capital"] / 100
dm["campus_pequeno"] = dm["campus"] * dm["pequeno"]
dm["regiao"] = dm["regiao"].map({r: i for i, r in enumerate(REG, start=1)}).astype("int8")
vl2 = {"regiao": dict(enumerate(REG, start=1))}
vl2.update({c: SIMNAO for c in ["norte", "nordeste", "sul", "centro_oeste", "pequeno", "campus",
                                "campus_pequeno"]})
rot2 = {
    "municipio": "Identificador do município",
    "regiao": "Região (1 = Sudeste, base)",
    "norte": "Norte",
    "nordeste": "Nordeste",
    "sul": "Sul",
    "centro_oeste": "Centro-Oeste",
    "pop_2000": "População em 2000",
    "pequeno": "Menos de 50 mil habitantes",
    "urbanizacao_2000": "Taxa de urbanização em 2000 (0 a 1)",
    "dist_capital": "Distância à capital do estado (km)",
    "campus": "Recebeu campus federal novo",
    "renda_pc_2000": "Renda per capita em 2000 (R$)",
    "renda_pc_2010": "Renda per capita em 2010 (R$)",
    "pobreza_2000": "Pobres em 2000 (% da população)",
    "pobreza_2010": "Pobres em 2010 (% da população)",
    "lrenda10": "ln(renda per capita 2010)",
    "lrenda00": "ln(renda per capita 2000)",
    "lpop": "ln(população 2000)",
    "dlrenda": "Crescimento da renda 2000-2010 (log)",
    "dist100": "Distância à capital (centenas de km)",
    "campus_pequeno": "Interação campus x pequeno",
}
dm.to_stata(DADOS / "municipios_campus.dta", write_index=False, version=118,
            variable_labels=rot2, value_labels=vl2,
            data_label="Laboratório Vale a pena estudar? Municípios e campus federal (dados fictícios)")
print("pnad_simulada.dta e municipios_campus.dta gravados")

# ---------------------------------------------------------------------------
# Caso 3: IDF-MT (com o índice já calculado)
# ---------------------------------------------------------------------------
INDIC = ["banda_larga", "cobertura_4g", "agencias", "cooperativa", "escolaridade", "capacitacao", "mei_mil"]


def construir_indice(d):
    """Mesma construção de analise_idf.py e da planilha: min-max, dimensões, pesos iguais."""
    d = d.copy()
    for c in INDIC:
        d[f"n_{c}"] = (d[c] - d[c].min()) / (d[c].max() - d[c].min())
    d["dim_digital"] = 100 * d[["n_banda_larga", "n_cobertura_4g"]].mean(axis=1)
    d["dim_financeira"] = 100 * d[["n_agencias", "n_cooperativa"]].mean(axis=1)
    d["dim_capacidades"] = 100 * d[["n_escolaridade", "n_capacitacao", "n_mei_mil"]].mean(axis=1)
    d["idf"] = d[["dim_digital", "dim_financeira", "dim_capacidades"]].mean(axis=1)
    return d


di = construir_indice(pd.read_csv(DADOS / "idf_mt.csv"))
di = di.drop(columns=[c for c in di.columns if c.startswith("n_")])
di["lpix"] = np.log(di["pix_pj"])
di["lpop"] = np.log(di["pop"])
di["lpib"] = np.log(di["pib_pc"])
MESO = ["Norte", "Nordeste", "Sudoeste", "Centro-Sul", "Sudeste"]
di["mesorregiao"] = di["mesorregiao"].map({r: i for i, r in enumerate(MESO, start=1)}).astype("int8")
rot3 = {
    "municipio": "Identificador do município", "mesorregiao": "Mesorregião de MT (1 = Norte)",
    "pop": "População", "pib_pc": "PIB per capita (R$)",
    "banda_larga": "Banda larga fixa: acessos por 100 domicílios", "cobertura_4g": "Cobertura 4G (% da população)",
    "agencias": "Agências, postos e correspondentes por 10 mil hab.", "cooperativa": "Tem cooperativa de crédito",
    "escolaridade": "Anos médios de estudo dos adultos", "capacitacao": "Participantes em cursos por 100 empresas",
    "mei_mil": "MEI por mil habitantes", "pix_pj": "Pix recebidos por empresa por mês",
    "dim_digital": "Dimensão digital (0 a 100)", "dim_financeira": "Dimensão financeira (0 a 100)",
    "dim_capacidades": "Dimensão capacidades (0 a 100)", "idf": "IDF-MT (0 a 100), pesos iguais",
    "lpix": "ln(Pix por empresa)", "lpop": "ln(população)", "lpib": "ln(PIB per capita)",
}
di.to_stata(DADOS / "idf_mt.dta", write_index=False, version=118, variable_labels=rot3,
            value_labels={"mesorregiao": dict(enumerate(MESO, start=1)), "cooperativa": SIMNAO},
            data_label="Laboratório: IDF-MT, municípios fictícios de Mato Grosso")
print("idf_mt.dta gravado")
