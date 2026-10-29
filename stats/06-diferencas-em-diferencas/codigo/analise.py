# Conteúdo 6 — Diferenças em diferenças
# Requer: pip install pandas statsmodels
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("../dados/programa_saude.csv")

# 1) DiD 2x2 "à mão" com as quatro médias
m = df.groupby(["tratado", "pos"])["gasto_saude_pc"].mean().unstack()
print(m.round(2))
did = (m.loc[1, 1] - m.loc[1, 0]) - (m.loc[0, 1] - m.loc[0, 0])
print("DiD (médias):", round(did, 3))

# 2) Regressão: y = b0 + b1·tratado + b2·pos + b3·(tratado×pos) + u
r = smf.ols("gasto_saude_pc ~ tratado * pos", data=df).fit(
    cov_type="cluster", cov_kwds={"groups": df["municipio"]})
print(r.params.round(3), r.bse.round(3), sep="\n")

# 3) TWFE: efeitos fixos de município e de ano
df["D"] = df["tratado"] * df["pos"]
twfe = smf.ols("gasto_saude_pc ~ D + C(municipio) + C(ano)", data=df).fit(
    cov_type="cluster", cov_kwds={"groups": df["municipio"]})
print("TWFE:", round(twfe.params["D"], 3), "(", round(twfe.bse["D"], 3), ")")

# 4) Estudo de eventos (ano de referência: 2014, o último antes do programa)
for a in range(2010, 2020):
    if a != 2014:
        df[f"ev_{a}"] = ((df["ano"] == a) & (df["tratado"] == 1)).astype(int)
termos = " + ".join(f"ev_{a}" for a in range(2010, 2020) if a != 2014)
es = smf.ols(f"gasto_saude_pc ~ {termos} + C(municipio) + C(ano)", data=df).fit(
    cov_type="cluster", cov_kwds={"groups": df["municipio"]})
for a in range(2010, 2020):
    if a != 2014:
        print(a, round(es.params[f"ev_{a}"], 2), round(es.bse[f"ev_{a}"], 2))

# Teste conjunto de tendências pré-tratamento (2010–2013)
print(es.f_test("ev_2010 = 0, ev_2011 = 0, ev_2012 = 0, ev_2013 = 0"))
