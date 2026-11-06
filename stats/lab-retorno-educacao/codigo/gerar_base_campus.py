"""Gera a base FICTÍCIA do Exemplo 2: campus federal novo e renda do município.

Inspirada na expansão das universidades federais nos anos 2000. Os estudos
brasileiros estimam ganhos de cerca de 3,5% a 5,8% na renda per capita dos
municípios que receberam campus (Barbosa, Petterini e Ferreira, RAC 2020),
maiores nas cidades pequenas. NÃO são dados reais.

Processo gerador (conhecido pelo professor):
  ln(renda_2010) = 0,62 + 0,93 ln(renda_2000) + 0,015 ln(pop_2000)
                   + efeitos regionais + 0,10 urbanizacao_2000
                   + campus × (0,035 + 0,035 pequeno) + u,   u ~ N(0; 0,10)
  pobreza_2010   = pobreza_2000 × 0,62 − 1,5 campus + ... + e  (pontos percentuais)
A instalação do campus NÃO foi sorteada: foi mais provável em municípios
maiores, mais ricos e mais distantes da capital (interiorização).

Uso:  python gerar_base_campus.py   (requer numpy e pandas)
"""
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parents[1] / "dados"
rng = np.random.default_rng(2005)
n = 1500

regioes = np.array(["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"])
regiao = rng.choice(regioes, n, p=[0.08, 0.32, 0.30, 0.21, 0.09])
nivel_reg = {"Norte": -0.30, "Nordeste": -0.55, "Sudeste": 0.0, "Sul": 0.05, "Centro-Oeste": -0.05}
cresc_reg = {"Norte": 0.03, "Nordeste": 0.06, "Sudeste": 0.0, "Sul": 0.01, "Centro-Oeste": 0.04}

ln_pop = rng.normal(9.6, 1.1, n)                         # mediana ~ 15 mil habitantes
pop_2000 = np.round(np.exp(np.clip(ln_pop, 6.7, 14.2)))
ln_pop = np.log(pop_2000)
urbanizacao = np.clip(0.35 + 0.07 * (ln_pop - 9.6) + rng.normal(0, 0.15, n), 0.08, 1.0)
dist_capital = np.round(np.clip(rng.gamma(2.2, 110, n), 5, 1400))
ln_renda_2000 = (np.log(420) + np.vectorize(nivel_reg.get)(regiao) + 0.06 * (ln_pop - 9.6)
                 + 0.45 * (urbanizacao - 0.45) - 0.0002 * dist_capital + rng.normal(0, 0.22, n))
renda_2000 = np.exp(ln_renda_2000)
pobreza_2000 = np.clip(95 - 14 * ln_renda_2000 + rng.normal(0, 3, n), 1, 85)

# --- seleção: quem recebeu campus novo -----------------------------------------
indice = (-10.5 + 0.95 * ln_pop + 1.4 * (ln_renda_2000 - np.log(420))
          + 0.0012 * dist_capital + rng.logistic(0, 1, n) * 0.9)
campus = (indice > np.quantile(indice, 0.92)).astype(int)   # ~8% dos municípios
pequeno = (pop_2000 < 50000).astype(int)

efeito = campus * (0.035 + 0.035 * pequeno)
ln_renda_2010 = (0.62 + 0.93 * ln_renda_2000 + 0.015 * ln_pop
                 + np.vectorize(cresc_reg.get)(regiao) + 0.10 * urbanizacao
                 + efeito + rng.normal(0, 0.10, n))
renda_2010 = np.exp(ln_renda_2010)
pobreza_2010 = np.clip(0.62 * pobreza_2000 + 2.0 - 1.5 * campus
                       - 4 * (ln_renda_2010 - ln_renda_2000 - 0.4) + rng.normal(0, 2.0, n), 0.5, 80)

df = pd.DataFrame({
    "municipio": np.arange(1, n + 1),
    "regiao": regiao,
    "norte": (regiao == "Norte").astype(int),
    "nordeste": (regiao == "Nordeste").astype(int),
    "sul": (regiao == "Sul").astype(int),
    "centro_oeste": (regiao == "Centro-Oeste").astype(int),
    "pop_2000": pop_2000.astype(int),
    "pequeno": pequeno,
    "urbanizacao_2000": urbanizacao.round(3),
    "dist_capital": dist_capital.astype(int),
    "campus": campus,
    "renda_pc_2000": renda_2000.round(2),
    "renda_pc_2010": renda_2010.round(2),
    "pobreza_2000": pobreza_2000.round(1),
    "pobreza_2010": pobreza_2010.round(1),
})

if __name__ == "__main__":
    PASTA.mkdir(parents=True, exist_ok=True)
    df.to_csv(PASTA / "municipios_campus.csv", index=False)
    print(f"dados/municipios_campus.csv: {len(df)} linhas")
