# Conteúdo 4 — Regressão linear múltipla (Estatística e Econometria, PROFINIT)
# Execute a partir desta pasta (codigo/).

library(fixest)   # install.packages("fixest")
df <- read.csv("../dados/salarios.csv")
df$lsal <- log(df$salario_hora)

m1 <- feols(lsal ~ educ, data = df, vcov = "hetero")
m2 <- feols(lsal ~ educ + exper + I(exper^2) + mulher, data = df, vcov = "hetero")
m3 <- feols(lsal ~ educ + exper + I(exper^2) + mulher + habilidade, data = df, vcov = "hetero")
etable(m1, m2, m3)                      # tabela lado a lado

wald(m2, keep = "exper")                # teste F conjunto

# Viés de variável omitida
delta <- coef(lm(habilidade ~ educ + exper + I(exper^2) + mulher, data = df))["educ"]
coef(m3)["educ"] + coef(m3)["habilidade"] * delta

# Interação
feols(lsal ~ educ * mulher + exper + I(exper^2), data = df, vcov = "hetero")

# VIF
library(car); vif(lm(lsal ~ educ + exper + mulher, data = df))
