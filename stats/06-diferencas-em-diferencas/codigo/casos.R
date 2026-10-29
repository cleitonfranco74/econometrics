# Estudos de caso — 06-diferencas-em-diferencas (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

library(haven); library(fixest); library(did)
f <- read.csv("../../dados_caso/did_ifood_sintetica.csv")
feols(criminalidade ~ treated + post + did, f, cluster = ~id_area)          # 2x2
feols(criminalidade ~ did | id_area + ano, f, cluster = ~id_area)          # TWFE
m <- read.csv("../../dados_caso/did_deams_sintetica_2000_2018.csv")
feols(taxa_homicidios_femininos ~ did | id_municipio + ano, m, cluster = ~id_municipio)

d <- read_dta("../../dados_caso/ifood_crime_sp.dta")
d$lcrimes <- log(d$crimes)

feols(lcrimes ~ post_ifood | cod_mun + ano, d, cluster = ~cod_mun)        # TWFE

# Sun & Abraham (estudo de eventos robusto à adoção escalonada)
d$coorte <- ifelse(d$ifood_ano == 0, 10000, d$ifood_ano)                   # nunca tratados
es <- feols(lcrimes ~ sunab(coorte, ano) | cod_mun + ano, d, cluster = ~cod_mun)
iplot(es); summary(es, agg = "ATT")

# Callaway & Sant'Anna
att <- att_gt(yname = "lcrimes", tname = "ano", idname = "cod_mun",
              gname = "ifood_ano", data = as.data.frame(d))
aggte(att, type = "simple")
ggdid(aggte(att, type = "dynamic", min_e = -5, max_e = 5))
