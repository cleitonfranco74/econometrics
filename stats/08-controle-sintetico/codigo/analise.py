# Conteúdo 8 — Controle sintético (implementação transparente com scipy)
# Requer: pip install pandas numpy scipy
import numpy as np
import pandas as pd
from scipy.optimize import minimize

df = pd.read_csv("../dados/painel_sintetico.csv")
Y = df.pivot(index="ano", columns="unidade", values="y")      # anos x unidades
anos = Y.index.values
pre = anos < 2012                                              # política em 2012
doadores = [c for c in Y.columns if c != "Tratado"]


def pesos_sinteticos(y1, Y0):
    """Pesos w >= 0, soma 1, que minimizam o erro quadrático no pré-tratamento."""
    J = Y0.shape[1]
    obj = lambda w: np.sum((y1 - Y0 @ w) ** 2)
    res = minimize(obj, np.full(J, 1 / J), method="SLSQP", bounds=[(0, 1)] * J,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                   options={"ftol": 1e-12, "maxiter": 1000})
    return res.x


def rmspe(gap, mask):
    return np.sqrt(np.mean(gap[mask] ** 2))


y1 = Y["Tratado"].values
Y0 = Y[doadores].values
w = pesos_sinteticos(y1[pre], Y0[pre])
sint = Y0 @ w
gap = y1 - sint

print("Pesos (> 0,01):", {d: round(p, 3) for d, p in zip(doadores, w) if p > 0.01})
print("RMSPE pré:", round(rmspe(gap, pre), 3), " pós:", round(rmspe(gap, ~pre), 3))
print("Efeito médio 2012–2019:", round(gap[~pre].mean(), 2))
print(pd.DataFrame({"ano": anos, "tratado": y1.round(2), "sintetico": sint.round(2),
                    "efeito": gap.round(2)}).to_string(index=False))

# Comparação: DiD simples contra a média dos doadores
media = Y0.mean(axis=1)
did = (y1[~pre].mean() - y1[pre].mean()) - (media[~pre].mean() - media[pre].mean())
print("DiD contra média dos doadores:", round(did, 2))

# Inferência por placebos no espaço: cada doador finge ser o tratado
razoes = {"Tratado": rmspe(gap, ~pre) / rmspe(gap, pre)}
gaps_placebo = {}
for d in doadores:
    outros = [o for o in doadores if o != d]
    wd = pesos_sinteticos(Y[d].values[pre], Y[outros].values[pre])
    g = Y[d].values - Y[outros].values @ wd
    gaps_placebo[d] = g
    razoes[d] = rmspe(g, ~pre) / rmspe(g, pre)
ordem = sorted(razoes, key=razoes.get, reverse=True)
print("Razão RMSPE pós/pré do tratado:", round(razoes["Tratado"], 2),
      " posição:", ordem.index("Tratado") + 1, "de", len(ordem),
      " p-valor de permutação:", round((ordem.index("Tratado") + 1) / len(ordem), 4))
# gaps_placebo guarda a trajetória do "efeito" de cada placebo, útil para o gráfico
