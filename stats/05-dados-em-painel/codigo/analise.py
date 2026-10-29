# Conteúdo 5 — Dados em painel
# Requer: pip install pandas statsmodels linearmodels
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS, PooledOLS, RandomEffects, FirstDifferenceOLS

df = pd.read_csv("../dados/painel_empresas.csv").set_index(["empresa", "ano"])
anos = pd.get_dummies(df.index.get_level_values("ano"), prefix="a", drop_first=True, dtype=float)
anos.index = df.index
X = pd.concat([df[["alavancagem", "tamanho"]], anos], axis=1).assign(const=1.0)

# MQO empilhado (pooled), erros agrupados por empresa
pooled = PooledOLS(df["roa"], X).fit(cov_type="clustered", cluster_entity=True)

# Efeitos fixos de empresa e de ano (two-way FE)
fe = PanelOLS(df["roa"], df[["alavancagem", "tamanho"]].assign(const=1.0),
              entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)

# Efeitos aleatórios (com dummies de ano)
re = RandomEffects(df["roa"], X).fit(cov_type="clustered", cluster_entity=True)

# Primeiras diferenças (sem constante; dummies de ano absorvem choques)
fd = FirstDifferenceOLS(df["roa"], pd.concat([df[["alavancagem", "tamanho"]], anos], axis=1)).fit(
    cov_type="clustered", cluster_entity=True)

for nome, m in [("Pooled", pooled), ("EF", fe), ("EA", re), ("PD", fd)]:
    print(f"{nome:7s} alav = {m.params['alavancagem']:.4f} ({m.std_errors['alavancagem']:.4f})   "
          f"tam = {m.params['tamanho']:.4f} ({m.std_errors['tamanho']:.4f})   n = {m.nobs}")

# Teste de Hausman (EF x EA) com erros convencionais
fe_c = PanelOLS(df["roa"], pd.concat([df[["alavancagem", "tamanho"]], anos], axis=1),
                entity_effects=True).fit()
re_c = RandomEffects(df["roa"], X).fit()
v = ["alavancagem", "tamanho"]
b = fe_c.params[v] - re_c.params[v]
V = fe_c.cov.loc[v, v] - re_c.cov.loc[v, v]
H = float(b @ np.linalg.inv(V) @ b)
from scipy import stats
print(f"Hausman: chi2(2) = {H:.2f}, p = {stats.chi2.sf(H, 2):.4g}")

# Decomposição da variância: entre (between) e dentro (within)
d = df.reset_index()
print("dp total:", d["alavancagem"].std().round(2),
      " between:", d.groupby("empresa")["alavancagem"].mean().std().round(2),
      " within:", (d["alavancagem"] - d.groupby("empresa")["alavancagem"].transform("mean")).std().round(2))
