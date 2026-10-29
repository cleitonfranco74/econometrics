# Estudos de caso — 03-correlacao-causalidade-regressao (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

library(haven); library(readxl)
g <- read_dta("../../dados_caso/gini_pib_mundo.dta")
g$lpib <- log(g$gdppercapita)
u <- g[order(g$year), ]; u <- u[!duplicated(u$code, fromLast = TRUE), ]
cor.test(u$ginicoefficient, u$gdppercapita, method = "spearman")
summary(lm(ginicoefficient ~ lpib + I(lpib^2), data = u))

gg <- read_excel("../../dados_caso/google_reglinear.xlsx")
names(gg) <- c("data", "ia", "receita", "usuarios")
summary(lm(receita ~ ia, data = gg))

apple <- read_excel("../../dados_caso/correlacoes_empresariais.xlsx", sheet = "Apple")
cor(apple[, -1])
