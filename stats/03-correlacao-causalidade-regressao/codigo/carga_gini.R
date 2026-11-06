# Conteúdo 3 — Estudo de caso: carga tributária e desigualdade (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

d <- read.csv("../../dados_caso/carga_gini_ocde_brasil.csv", encoding = "UTF-8")
cor.test(d$carga_pib, d$gini)                                      # todos (38): r = −0,66
with(subset(d, pais != "Brasil"), cor(carga_pib, gini))            # sem o Brasil: −0,70
by(d, d$grupo, function(x) cor(x$carga_pib, x$gini))               # Simpson: −0,46 e +0,31
summary(lm(gini ~ carga_pib, data = d))
plot(d$carga_pib, d$gini, xlab = "Carga tributária (% do PIB)", ylab = "Índice de Gini")
text(d$carga_pib, d$gini, d$pais, pos = 3, cex = 0.6)
abline(lm(gini ~ carga_pib, data = d))
