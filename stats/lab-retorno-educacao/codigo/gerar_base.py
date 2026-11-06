"""Gera a base FICTÍCIA do Laboratório "Vale a pena estudar?".

Microdados simulados no estilo da PNAD Contínua: trabalhadores ocupados de
25 a 64 anos. Os parâmetros foram escolhidos para reproduzir ordens de
grandeza da literatura brasileira (prêmio salarial do ensino superior em
torno de 150% sobre o ensino médio, retorno crescente por nível de ensino,
diferenças regionais e por sexo). NÃO são dados reais.

Processo gerador (efeitos "verdadeiros", conhecidos pelo professor):
  ln(salário-hora) = 1,25 + 0,075 educ + 0,40 superior + 0,035 exper
                     - 0,0005 exper² - 0,20 mulher + 0,01 educ×mulher
                     + efeitos regionais (base Sudeste) + 0,12 urbano
                     + 0,13 habilidade + u
  u ~ Normal(0, σ), com σ crescente na escolaridade (heterocedasticidade).
A habilidade aumenta a escolaridade -> viés de variável omitida positivo.

Uso:  python gerar_base.py   (requer numpy e pandas)
"""
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parents[1] / "dados"
rng = np.random.default_rng(148)
n = 2000

# --- características de origem ------------------------------------------------
regioes = np.array(["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"])
regiao = rng.choice(regioes, n, p=[0.08, 0.25, 0.43, 0.15, 0.09])
efeito_reg = {"Norte": -0.18, "Nordeste": -0.28, "Sudeste": 0.0,
              "Sul": 0.03, "Centro-Oeste": 0.06}
educ_reg = {"Norte": -0.8, "Nordeste": -1.2, "Sudeste": 0.4,
            "Sul": 0.3, "Centro-Oeste": 0.1}
urbano = rng.binomial(1, np.where(np.isin(regiao, ["Norte", "Nordeste"]), 0.78, 0.90))
mulher = rng.binomial(1, 0.45, n)
idade = rng.integers(25, 65, n)
habilidade = rng.normal(0, 1, n)                 # NÃO observada na vida real
educ_mae = np.clip(np.round(6.5 + 1.2 * habilidade
                            + np.vectorize(educ_reg.get)(regiao)
                            - 0.08 * (idade - 45) + rng.normal(0, 3.0, n)), 0, 18)

# --- escolaridade (anos de estudo), com "amontoamento" nos diplomas -----------
latente = (9.2 + 2.0 * habilidade + 0.35 * educ_mae + 1.0 * urbano
           + np.vectorize(educ_reg.get)(regiao) - 0.06 * (idade - 45)
           + 0.4 * mulher + rng.normal(0, 2.3, n))
educ = np.clip(np.round(latente), 0, 20)
for marco in (9, 12, 16):                        # quem chega perto, conclui
    perto = (educ >= marco - 1) & (educ <= marco + 1) & (rng.random(n) < 0.55)
    educ[perto] = marco
educ = educ.astype(int)

nivel = np.select([educ >= 16, educ >= 12, educ >= 9],
                  ["Superior", "Médio", "Fundamental"], "Fund. incompleto")
superior = (educ >= 16).astype(int)
exper = np.clip(idade - np.maximum(educ, 8) - 6, 0, None)

# --- salário -----------------------------------------------------------------
sigma = 0.38 + 0.012 * educ
lsal = (1.25 + 0.075 * educ + 0.40 * superior + 0.035 * exper
        - 0.0005 * exper**2 - 0.20 * mulher + 0.01 * educ * mulher
        + np.vectorize(efeito_reg.get)(regiao) + 0.12 * urbano
        + 0.13 * habilidade + rng.normal(0, 1, n) * sigma)
salario_hora = np.exp(lsal)
horas = np.clip(np.round(rng.normal(40, 7, n) - 3 * mulher), 15, 60)
renda_mensal = salario_hora * horas * 4.33

df = pd.DataFrame({
    "id": np.arange(1, n + 1),
    "regiao": regiao,
    "norte": (regiao == "Norte").astype(int),
    "nordeste": (regiao == "Nordeste").astype(int),
    "sul": (regiao == "Sul").astype(int),
    "centro_oeste": (regiao == "Centro-Oeste").astype(int),
    "urbano": urbano,
    "mulher": mulher,
    "idade": idade,
    "educ": educ,
    "nivel": nivel,
    "fundamental": (nivel == "Fundamental").astype(int),
    "medio": (nivel == "Médio").astype(int),
    "superior": superior,
    "exper": exper,
    "educ_mae": educ_mae.astype(int),
    "horas": horas.astype(int),
    "salario_hora": salario_hora.round(2),
    "renda_mensal": renda_mensal.round(0).astype(int),
    "habilidade": habilidade.round(3),
})

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    df.to_csv(PASTA / "pnad_simulada.csv", index=False)
    print(f"dados/pnad_simulada.csv: {len(df)} linhas")
