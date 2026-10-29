# Conteúdo 5 — Dados em painel (Estatística e Econometria, PROFINIT)
# Execute a partir desta pasta (codigo/).

library(fixest)   # install.packages(c("fixest", "plm"))
library(plm)
df <- read.csv("../dados/painel_empresas.csv")

pooled <- feols(roa ~ alavancagem + tamanho | ano, data = df, cluster = ~empresa)
fe     <- feols(roa ~ alavancagem + tamanho | empresa + ano, data = df, cluster = ~empresa)
etable(pooled, fe)

# Efeitos aleatórios, primeiras diferenças e Hausman com plm
pdf <- pdata.frame(df, index = c("empresa", "ano"))
fe_plm <- plm(roa ~ alavancagem + tamanho + factor(ano), data = pdf, model = "within")
re_plm <- plm(roa ~ alavancagem + tamanho + factor(ano), data = pdf, model = "random")
fd_plm <- plm(roa ~ alavancagem + tamanho + factor(ano), data = pdf, model = "fd")
phtest(fe_plm, re_plm)   # Hausman
