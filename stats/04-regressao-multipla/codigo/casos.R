# Estudos de caso — 04-regressao-multipla (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

library(haven); library(readxl); library(fixest)
w <- read_dta("../../dados_caso/wage1.dta")
m <- lm(LWAGE ~ EDUC + EXPER + TENURE, data = w); summary(m)
car::linearHypothesis(m, "EXPER + TENURE = 0")

p <- read_dta("../../dados_caso/pnad_2009_2011_internet_renda.dta")
p <- subset(p, Renda > 0)
feols(log(Renda) ~ internet + lereescrever + anosestudo + i(horas_trabalhadas) + genero +
        idade + I(idade^2) + i(`raça`) + i(estcivil) | uf + ano, data = p, vcov = "hetero")

s <- read_dta("../../dados_caso/samu_mt_2000_2020.dta")
feols(log(mortes_transito + 1) ~ samu + equipamentos + ortopedista + tx_analfa + log(pop),
      data = s, cluster = ~cod_mun)

a <- read_excel("../../dados_caso/estudos_caso_regressao_multipla.xlsx", sheet = "Amazon")
a <- a[, !(names(a) %in% c("Data", "log Receitas Vendas online %"))]
summary(lm(`Receita de Vendas Online (bi USD)` ~ ., data = a))
