"""Gera a base sintética de exemplos de correlação do Conteúdo 3, com as abas
citadas nos slides:

- Galeria_r: seis painéis com r de +0,90 a −0,91, um painel com outlier e um
  com relação não linear (n = 60 cada).
- Sorvete_Afogamento: 52 semanas; a temperatura causa vendas e afogamentos.

Todos os dados são SIMULADOS. Uso: python base_correlacao_causalidade.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent


def painel(rng, n, rho):
    x = rng.normal(0, 1, n)
    y = rho * x + np.sqrt(1 - rho**2) * rng.normal(0, 1, n)
    return x, y


def galeria(seed=292):
    rng = np.random.default_rng(seed)
    linhas = []
    for nome, rho in [("r_090", 0.90), ("r_050", 0.50), ("r_000", 0.0), ("r_m050", -0.50), ("r_m090", -0.92)]:
        x, y = painel(rng, 60, rho)
        linhas += [(nome, a, b) for a, b in zip(x, y)]
    x = rng.uniform(-2, 2, 60)
    linhas += [("nao_linear", a, a**2 + rng.normal(0, 0.35)) for a in x]
    x, y = painel(rng, 59, 0.0)
    x, y = np.append(x, 9.0), np.append(y, 7.0)                # um único outlier
    linhas += [("outlier", a, b) for a, b in zip(x, y)]
    return pd.DataFrame(linhas, columns=["painel", "x", "y"]).round(3)


def sorvete(seed=19):
    rng = np.random.default_rng(seed)
    sem = np.arange(1, 53)
    temp = 25 + 6 * np.cos(2 * np.pi * (sem - 2) / 52) + rng.normal(0, 1.6, 52)
    sorv = 300 + 40 * (temp - 25) + rng.normal(0, 80, 52)
    afog = np.clip(np.round(8 + 0.9 * (temp - 25) + rng.normal(0, 3.2, 52)), 0, None)
    return pd.DataFrame({"semana": sem, "temperatura_c": temp.round(1),
                         "sorvetes_vendidos": sorv.round(0).astype(int), "afogamentos": afog.astype(int)})


if __name__ == "__main__":
    g, s = galeria(), sorvete()
    with pd.ExcelWriter(AQUI / "correlacao_causalidade_sintetica.xlsx") as w:
        g.to_excel(w, sheet_name="Galeria_r", index=False)
        s.to_excel(w, sheet_name="Sorvete_Afogamento", index=False)
    print({p: round(d.x.corr(d.y), 3) for p, d in g.groupby("painel")},
          " outlier sem o ponto:", round(g[g.painel == "outlier"].iloc[:-1].x.corr(g[g.painel == "outlier"].iloc[:-1].y), 3))
    rxy, rxz, ryz = s.sorvetes_vendidos.corr(s.afogamentos), s.temperatura_c.corr(s.sorvetes_vendidos), s.temperatura_c.corr(s.afogamentos)
    print("sorvete r =", round(rxy, 3), " r(temp,sorv) =", round(rxz, 3), " r(temp,afog) =", round(ryz, 3),
          " parcial =", round((rxy - rxz * ryz) / np.sqrt((1 - rxz**2) * (1 - ryz**2)), 3))
