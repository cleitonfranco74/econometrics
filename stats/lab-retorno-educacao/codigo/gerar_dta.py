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
