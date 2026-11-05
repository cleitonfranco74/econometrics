"""Base SIMULADA para o estudo de caso didático de SDID (Synthetic Difference-in-Differences):
efeito do teto de gastos (EC 95, aprovada em dezembro de 2016) sobre o
juro real de 10 anos e o resultado primário do Brasil.

Brasil + 15 economias emergentes, 2000–2019 (pré: 2000–2016; pós: 2017–2019).
Os dados seguem um modelo de fatores com efeitos verdadeiros conhecidos:
- juro real de 10 anos: −0,6, −1,2 e −1,8 p.p. em 2017, 2018 e 2019;
- resultado primário (% do PIB): +0,4, +0,8 e +1,2 p.p.
O Brasil tem juro real bem acima de todos os doadores (problema do fecho
convexo) e sofre um choque fiscal próprio e transitório em 2014–2016 (recessão).
Os nomes dos países são rótulos; os números NÃO são dados reais.
Uso: python base_teto_gastos.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
PAISES = ["Brasil", "Chile", "Colômbia", "México", "Peru", "Uruguai", "Paraguai", "África do Sul",
          "Indonésia", "Índia", "Filipinas", "Tailândia", "Malásia", "Polônia", "Hungria", "Romênia"]
ANOS = np.arange(2000, 2020)


def gerar(seed=2016):
    rng = np.random.default_rng(seed)
    J, T = len(PAISES), len(ANOS)
    t = np.arange(T)
    f1 = -0.12 * t + 0.8 * np.sin(t / 2.5)                  # ciclo global de juros
    f2 = np.where((ANOS >= 2008) & (ANOS <= 2010), -1.5, 0.0) + 0.05 * t   # crise de 2008 e tendência
    f3 = np.cos(t / 3.0)                                     # ciclo das commodities
    lam = rng.uniform(0.5, 1.5, (J, 3))
    w = np.zeros(J - 1); w[[1, 3, 6, 9]] = [0.35, 0.25, 0.25, 0.15]   # Brasil ≈ combinação de 4 doadores
    lam[0] = w @ lam[1:]
    # Juro real de 10 anos (%): Brasil 4 p.p. acima de qualquer combinação dos doadores
    nivel_j = rng.uniform(1.0, 4.0, J); nivel_j[0] = w @ nivel_j[1:] + 4.0
    juro = nivel_j[:, None] + lam @ np.vstack([f1, f2, f3]) * 1.2 + rng.normal(0, 0.25, (J, T))
    # Resultado primário (% do PIB)
    nivel_p = rng.uniform(-1.5, 2.5, J); nivel_p[0] = w @ nivel_p[1:]
    prim = nivel_p[:, None] + lam @ np.vstack([-0.4 * f1, f2, 0.8 * f3]) + rng.normal(0, 0.25, (J, T))
    prim[0, (ANOS >= 2014) & (ANOS <= 2016)] -= [0.8, 1.4, 1.6]     # choque fiscal próprio do Brasil
    pos = ANOS >= 2017
    efeito_j = np.where(pos, -0.6 * (ANOS - 2016), 0.0)
    efeito_p = np.where(pos, 0.4 * (ANOS - 2016), 0.0)
    juro[0] += efeito_j; prim[0] += efeito_p
    divida = 40 + 0.5 * np.cumsum(-prim, axis=1) + rng.normal(0, 1, (J, T))
    linhas = [(p, int(a), round(juro[j, k], 2), round(prim[j, k], 2), round(divida[j, k], 1), int(j == 0),
               round(efeito_j[k] if j == 0 else 0, 2), round(efeito_p[k] if j == 0 else 0, 2))
              for j, p in enumerate(PAISES) for k, a in enumerate(ANOS)]
    return pd.DataFrame(linhas, columns=["pais", "ano", "juro_real_10a", "resultado_primario", "divida_bruta",
                                         "brasil", "efeito_verdadeiro_juro", "efeito_verdadeiro_primario"])


if __name__ == "__main__":
    d = gerar()
    d.to_csv(AQUI / "teto_gastos_sintetica.csv", index=False)
    print(d.groupby("pais")[["juro_real_10a", "resultado_primario"]].mean().round(2).sort_values("juro_real_10a").tail(4))
