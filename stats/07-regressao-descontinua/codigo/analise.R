# Conteúdo 7 — Regressão descontínua (Estatística e Econometria, PROFINIT)
# Execute a partir desta pasta (codigo/).

library(rdrobust); library(rddensity)   # install.packages(c("rdrobust","rddensity"))
df <- read.csv("../dados/rdd_credito.csv")
df$z <- (df$pontuacao - 60) / 10

rdplot(df$investimento, df$z, c = 0)
summary(rdrobust(df$credito, df$z, c = 0))                  # 1º estágio
summary(rdrobust(df$investimento, df$z, c = 0))                      # forma reduzida
summary(rdrobust(df$investimento, df$z, c = 0, fuzzy = df$credito))
summary(rdrobust(df$investimento, df$z, c = 0, fuzzy = df$credito,
                 p = 2, kernel = "epanechnikov", bwselect = "msesum"))

summary(rddensity(df$z, c = 0))                                   # manipulação
with(subset(df, z < 0), summary(rdrobust(investimento, z, c = -1)))  # placebo em 50 pontos

# MQ2E numa janela fixa
library(fixest)
feols(investimento ~ z + z:acima_corte | credito ~ acima_corte,
      data = subset(df, abs(z) <= 2), vcov = "hetero")
