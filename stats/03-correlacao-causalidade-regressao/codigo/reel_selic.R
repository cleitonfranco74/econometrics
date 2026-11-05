# Conteúdo 3 — Estudo de caso: o reel da Selic e do déficit (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

library(readxl)
f <- read_excel("../../dados_caso/correlacao_causalidade_sintetica.xlsx", sheet = "Fiscal_Selic")
cor(f$superavit_primario, f$selic)
by(f, f$regime, function(d) cor(d$superavit_primario, d$selic))     # Simpson
coef(lm(selic ~ deficit_primario, f))
coef(lm(selic ~ deficit_primario + inflacao, f))

s <- read_excel("../../dados_caso/correlacao_causalidade_sintetica.xlsx", sheet = "Sorvete_Afogamento")
cor(resid(lm(sorvetes_vendidos ~ temperatura_c, s)),
    resid(lm(afogamentos ~ temperatura_c, s)))                     # correlação parcial

# Tarefa: install.packages("rbcb"); rbcb::get_series(c(selic = 432, ipca = 433))
# (confira os códigos das séries no SGS e acrescente primário e dívida bruta)
