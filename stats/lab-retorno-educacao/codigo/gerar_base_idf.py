"""Gera a base FICTÍCIA do Caso 3: IDF-MT, índice de condições digitais e
financeiras para os pequenos negócios dos municípios de Mato Grosso.

Os municípios, nomes de mesorregião à parte, são inventados. Os indicadores
imitam o que existe em fontes públicas (Anatel, Banco Central, Receita
Federal, IBGE, SEBRAE/SENAR), mas os valores NÃO são reais.

Processo gerador do resultado (conhecido pelo professor):
  ln(pix_pj) = 2,2 + 0,012 banda_larga + 0,30 cooperativa
               + 0,004 capacitacao + 0,000 agencias  (agências não importam)
               + 0,10 ln(pop) + 0,25 ln(pib_pc) + u,   u ~ N(0; 0,25)
pix_pj = transações Pix recebidas por empresa por mês.
Municípios maiores e mais ricos têm melhores condições E mais uso de Pix:
por isso a regressão simples do uso no índice exagera a relação.

Uso:  python gerar_base_idf.py   (requer numpy e pandas)
"""
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parents[1] / "dados"
rng = np.random.default_rng(142)
n = 142

meso = np.array(["Norte", "Nordeste", "Sudoeste", "Centro-Sul", "Sudeste"])
mesorregiao = rng.choice(meso, n, p=[0.40, 0.17, 0.15, 0.12, 0.16])
efeito_meso = {"Norte": 0.0, "Nordeste": -0.10, "Sudoeste": -0.08, "Centro-Sul": 0.05, "Sudeste": 0.04}

ln_pop = np.clip(rng.normal(9.3, 0.95, n), 7.0, 13.4)          # mediana ~ 11 mil hab.
pop = np.round(np.exp(ln_pop)).astype(int)
ln_pop = np.log(pop)
ln_pibpc = (np.log(45000) + 0.08 * (ln_pop - 9.3) + np.vectorize(efeito_meso.get)(mesorregiao)
            + rng.normal(0, 0.40, n))
pib_pc = np.round(np.exp(ln_pibpc), -2)
ln_pibpc = np.log(pib_pc)
dev = 0.55 * (ln_pop - 9.3) + 0.9 * (ln_pibpc - np.log(45000))  # "desenvolvimento" latente

# --- indicadores de condições -------------------------------------------------
banda_larga = np.clip(np.round(32 + 9 * dev + rng.normal(0, 7, n), 1), 4, 80)       # acessos/100 domicílios
cobertura_4g = np.clip(np.round(78 + 9 * dev + rng.normal(0, 9, n), 1), 30, 100)    # % da população
agencias = np.clip(np.round(3.2 + 0.8 * dev + rng.normal(0, 0.9, n), 2), 0.3, 9)    # pontos de atendimento/10 mil hab.
p_coop = 1 / (1 + np.exp(-(0.4 + 1.6 * dev)))
cooperativa = rng.binomial(1, p_coop)                                               # tem cooperativa de crédito
escolaridade = np.clip(np.round(7.6 + 0.7 * dev + rng.normal(0, 0.6, n), 1), 4.5, 12) # anos médios de estudo (25+)
capacitacao = np.clip(np.round(25 + 10 * dev + rng.normal(0, 14, n)), 0, 110)       # participantes em cursos por 100 empresas
mei_mil = np.clip(np.round(38 + 6 * dev + rng.normal(0, 6, n), 1), 12, 80)         # MEI por mil habitantes

# --- resultado: uso de Pix pelas empresas ---------------------------------------
ln_pix = (2.2 + 0.012 * banda_larga + 0.30 * cooperativa + 0.004 * capacitacao
          + 0.0 * agencias + 0.10 * ln_pop + 0.25 * (ln_pibpc - np.log(45000))
          + rng.normal(0, 0.25, n))
pix_pj = np.round(np.exp(ln_pix), 1)

df = pd.DataFrame({
    "municipio": np.arange(1, n + 1),
    "mesorregiao": mesorregiao,
    "pop": pop,
    "pib_pc": pib_pc.astype(int),
    "banda_larga": banda_larga,
    "cobertura_4g": cobertura_4g,
    "agencias": agencias,
    "cooperativa": cooperativa,
    "escolaridade": escolaridade,
    "capacitacao": capacitacao.astype(int),
    "mei_mil": mei_mil,
    "pix_pj": pix_pj,
})

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    df.to_csv(PASTA / "idf_mt.csv", index=False)
    print(f"dados/idf_mt.csv: {len(df)} linhas")
