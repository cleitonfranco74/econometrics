# Conteúdo 8 — SDID: teto de gastos de 2016, base SIMULADA (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

# remotes::install_github("synth-inference/synthdid")
library(synthdid)
d <- read.csv("../../dados_caso/teto_gastos_sintetica.csv")
d$teto <- as.integer(d$pais == "Brasil" & d$ano >= 2017)

pm <- panel.matrices(d, unit = "pais", time = "ano",
                     outcome = "juro_real_10a", treatment = "teto")
sdid <- synthdid_estimate(pm$Y, pm$N0, pm$T0)
sc   <- sc_estimate(pm$Y, pm$N0, pm$T0)
did  <- did_estimate(pm$Y, pm$N0, pm$T0)
c(SDID = sdid, SC = sc, DiD = did)
sqrt(vcov(sdid, method = "placebo"))          # erro-padrão por placebos
synthdid_plot(sdid)                            # Brasil × contrafactual e pesos de tempo
synthdid_units_plot(sdid)                      # pesos de unidades

# Janela sem a recessão: descarte 2014–2016 antes de montar o painel
d2 <- subset(d, !(ano %in% 2014:2016))
