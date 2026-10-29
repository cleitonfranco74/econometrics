# Estudos de caso — 05-dados-em-painel (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

library(haven); library(fixest)
s <- read_dta("../../dados_caso/samu_mt_2000_2020.dta")
s$frota_pc <- s$frota / s$pop * 100
etable(feols(tx_mortes_transito ~ samu + frota_pc | ano, s, cluster = ~cod_mun),
       feols(tx_mortes_transito ~ samu + frota_pc | cod_mun + ano, s, cluster = ~cod_mun))

g <- read_dta("../../dados_caso/gini_pib_mundo.dta")
etable(feols(ginicoefficient ~ log(gdppercapita) | year, g, cluster = ~code),
       feols(ginicoefficient ~ log(gdppercapita) | code + year, g, cluster = ~code))

c <- read_dta("../../dados_caso/co2_pd_2000_2020.dta")
feols(ln_co2_pc ~ pd + taxadeurbanizacao + crescimentopop | cod_pais + ano, c, cluster = ~cod_pais)
