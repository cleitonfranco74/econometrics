# Conteúdo 6 — Tendências paralelas: verificação (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

library(fixest)
d <- read.csv("../dados/programa_saude.csv")

# 1. Gráfico das médias
m <- aggregate(gasto_saude_pc ~ ano + tratado, d, mean)
plot(m$ano[m$tratado == 1], m$gasto_saude_pc[m$tratado == 1], type = "b",
     ylim = range(m$gasto_saude_pc), xlab = "ano", ylab = "gasto")
lines(m$ano[m$tratado == 0], m$gasto_saude_pc[m$tratado == 0], type = "b", col = "red")
abline(v = 2014.5, lty = 2)

# 2. Estudo de eventos e teste conjunto das pré-tendências
es <- feols(gasto_saude_pc ~ i(ano, tratado, ref = 2014) | municipio + ano,
            d, cluster = ~municipio)
wald(es, keep = "201[0-3]")

# 3. Placebo de data (só período pré)
pre <- subset(d, ano <= 2014)
pre$falso <- pre$tratado * (pre$ano >= 2012)
feols(gasto_saude_pc ~ falso | municipio + ano, pre, cluster = ~municipio)

# 4. Sensibilidade (Rambachan & Roth): remotes::install_github("asheshrambachan/HonestDiD")
