"""Gera a base sintética do estudo de caso “Correlação não é causalidade”
(reel sobre Selic e déficit público), com as mesmas abas citadas nos slides:

- Galeria_r: seis painéis com r de +0,90 a −0,91, um painel com outlier e um
  com relação não linear (n = 60 cada).
- Sorvete_Afogamento: 52 semanas; a temperatura causa vendas e afogamentos.
- Fiscal_Selic: 30 “anos” em dois regimes de inflação. Efeito verdadeiro do
  déficit primário sobre a Selic = +0,5; a inflação é o confundidor.

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


def fiscal(seed=4):
    rng = np.random.default_rng(seed)
    n = 15
    alta = pd.DataFrame({"regime": "inflação alta", "inflacao": rng.normal(8.0, 0.3, n),
                         "superavit_primario": rng.normal(3.0, 0.8, n)})
    baixa = pd.DataFrame({"regime": "inflação baixa", "inflacao": rng.normal(4.0, 0.3, n),
                          "superavit_primario": rng.normal(-1.0, 0.8, n)})
    d = pd.concat([alta, baixa], ignore_index=True)
    d["deficit_primario"] = -d["superavit_primario"]
    d["selic"] = 1.0 + 1.5 * d["inflacao"] + 0.5 * d["deficit_primario"] + rng.normal(0, 0.3, len(d))
    d.insert(0, "obs", range(1, len(d) + 1))
    return d.round(2)


if __name__ == "__main__":
    import statsmodels.formula.api as smf
    g, s, f = galeria(), sorvete(), fiscal()
    with pd.ExcelWriter(AQUI / "correlacao_causalidade_sintetica.xlsx") as w:
        g.to_excel(w, sheet_name="Galeria_r", index=False)
        s.to_excel(w, sheet_name="Sorvete_Afogamento", index=False)
        f.to_excel(w, sheet_name="Fiscal_Selic", index=False)
    print({p: round(d.x.corr(d.y), 3) for p, d in g.groupby("painel")},
          " outlier sem o ponto:", round(g[g.painel == "outlier"].iloc[:-1].x.corr(g[g.painel == "outlier"].iloc[:-1].y), 3))
    rxy, rxz, ryz = s.sorvetes_vendidos.corr(s.afogamentos), s.temperatura_c.corr(s.sorvetes_vendidos), s.temperatura_c.corr(s.afogamentos)
    print("sorvete r =", round(rxy, 3), " r(temp,sorv) =", round(rxz, 3), " r(temp,afog) =", round(ryz, 3),
          " parcial =", round((rxy - rxz * ryz) / np.sqrt((1 - rxz**2) * (1 - ryz**2)), 3))
    print("fiscal r(superávit, Selic) todos =", round(f.superavit_primario.corr(f.selic), 3),
          {k: round(d.superavit_primario.corr(d.selic), 3) for k, d in f.groupby("regime")})
    b0 = smf.ols("selic ~ deficit_primario", f).fit().params["deficit_primario"]
    b1 = smf.ols("selic ~ deficit_primario + inflacao", f).fit().params
    delta = smf.ols("inflacao ~ deficit_primario", f).fit().params["deficit_primario"]
    print("β sem controle =", round(b0, 3), " com inflação =", round(b1["deficit_primario"], 3),
          " γ =", round(b1["inflacao"], 3), " Cov/Var =", round(delta, 3))
