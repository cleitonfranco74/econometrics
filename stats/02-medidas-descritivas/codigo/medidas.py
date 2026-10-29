# Medidas descritivas em Python — Estatística (PROFINIT), Conteúdo 2
# Requer: pip install pandas numpy scipy
import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_csv("../dados/retornos_mensais.csv")
a = df["acao_A"]

# Tendência central
print("Média:     ", a.mean())
print("Mediana:   ", a.median())
print("Moda:      ", a.mode().tolist())          # todos os valores, se não houver repetição
print("Média aparada 10%:", stats.trim_mean(a, 0.10))

# Média geométrica de retornos (em %): (Π(1+r))^(1/n) − 1
geo = (np.prod(1 + a / 100) ** (1 / len(a)) - 1) * 100
print("Média geométrica:", geo)

# Separatrizes (método linear = tipo 7 do R, padrão do numpy/pandas)
q1, q3 = a.quantile([0.25, 0.75])
iqr = q3 - q1
print("Q1, Q3, IIQ:", q1, q3, iqr)
print("Cercas de Tukey:", q1 - 1.5 * iqr, q3 + 1.5 * iqr)

# Dispersão (ddof=1 → divisor n−1, amostral)
print("Variância: ", a.var(ddof=1))
print("Desvio-padrão:", a.std(ddof=1))
print("CV:        ", a.std(ddof=1) / a.mean())
print("Volatilidade anualizada:", a.std(ddof=1) * np.sqrt(12))

# Forma (estimadores ajustados, iguais aos do Excel e do pandas)
print("Assimetria:", stats.skew(a, bias=False))
print("Curtose em excesso:", stats.kurtosis(a, bias=False))

# Associação entre as duas ações
print("Covariância:", df["acao_A"].cov(df["acao_B"]))
print("Correlação: ", df["acao_A"].corr(df["acao_B"]))

# Resumo completo
print(df[["acao_A", "acao_B"]].describe())
