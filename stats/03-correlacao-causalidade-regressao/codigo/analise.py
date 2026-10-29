# Conteúdo 3 — Correlação, causalidade e regressão linear simples
# Requer: pip install pandas statsmodels
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("../dados/publicidade_vendas.csv")

# 1) Correlação
print(df[["vendas", "publicidade", "tamanho"]].corr().round(3))

# 2) Regressão linear simples: vendas = b0 + b1·publicidade + u
m1 = smf.ols("vendas ~ publicidade", data=df).fit()
print(m1.summary())

# Coeficiente "à mão": b1 = cov(x, y) / var(x)
b1 = df["publicidade"].cov(df["vendas"]) / df["publicidade"].var()
b0 = df["vendas"].mean() - b1 * df["publicidade"].mean()
print(f"b0 = {b0:.3f}   b1 = {b1:.3f}")

# Erros-padrão robustos à heterocedasticidade (HC1, igual ao ", robust" do Stata)
print(smf.ols("vendas ~ publicidade", data=df).fit(cov_type="HC1").summary().tables[1])

# Previsão para uma empresa que gasta R$ 15 mil em publicidade
print(m1.predict(pd.DataFrame({"publicidade": [15]})))

# 3) O confundidor: controlando pelo tamanho, o efeito da publicidade cai
m2 = smf.ols("vendas ~ publicidade + tamanho", data=df).fit()
print(m2.params.round(3))
