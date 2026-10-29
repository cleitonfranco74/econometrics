# Estudos de caso — 03-correlacao-causalidade-regressao (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

library(haven); library(readxl)
sv <- read.csv("../../dados_caso/sorvete_afogamentos.csv")
cor(sv$sorvetes_mil_unid, sv$afogamentos)
cor(resid(lm(sorvetes_mil_unid ~ temperatura_media_c, sv)),
    resid(lm(afogamentos ~ temperatura_media_c, sv)))          # correlação parcial
summary(lm(afogamentos ~ sorvetes_mil_unid + temperatura_media_c, sv))

ct <- read.csv("../../dados_caso/carga_tributaria_gini.csv")
cor(ct$gini, ct$carga_tributaria_pib)
with(subset(ct, !pais %in% c("Brasil", "Índia")), cor(gini, carga_tributaria_pib))
plot(ct$gini, ct$carga_tributaria_pib); text(ct$gini, ct$carga_tributaria_pib, ct$pais, pos = 3)
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
