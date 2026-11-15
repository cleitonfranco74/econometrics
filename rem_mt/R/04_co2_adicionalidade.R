# =============================================================================
# 04_co2_adicionalidade.R — converte o efeito DDD em área e tCO2e evitadas
#                           e compara com a linha de base histórica
# =============================================================================

invisible(Sys.setlocale("LC_ALL", "C.UTF-8"))
suppressPackageStartupMessages({ library(data.table); library(fixest); library(jsonlite) })
p   <- fread("dados/painel_rem_mt.csv")[uf != "TO"]
mod <- readRDS("resultados/modelos.rds")

# ---------------------------------------------------------------------------
# Parâmetros (PROVISÓRIOS — substituir pelos valores do FREL/Inventário)
#   EF: fator de emissão médio do bioma, tCO2e por hectare desmatado
#   r : reserva de não permanência (ART TREES usa de 5% a 25%)
#   v : vazamento — o teste de vazamento (script 03) não encontrou aumento
#       nos controles vizinhos de MT; usa-se v = 0 e reporta-se v = 10%
# ---------------------------------------------------------------------------
EF <- c(Amazonia = 550, Cerrado = 200)
r  <- 0.10
v  <- 0

# Área municipal dos municípios-bioma de MT e alto risco (km²)
area_alvo <- unique(p[mt == 1 & alto == 1, .(id, bioma, area_km2)])[, .(area = sum(area_km2)), by = bioma]

# 1. Pelo efeito médio por bioma (β em p.p. da área municipal por ano)
co2_bio <- rbindlist(lapply(c("Amazonia", "Cerrado"), function(b) {
  m  <- if (b == "Amazonia") mod$m_am else mod$m_ce
  ic <- confint(m)[1, ]
  A  <- area_alvo[bioma == b, area]
  anos <- 7                                            # 2018 a 2024
  km2 <- -c(coef(m)[1], ic[[2]], ic[[1]]) / 100 * A * anos
  data.table(bioma = b, beta = coef(m)[1], area_mun_km2 = A,
             ha_evitados = km2[1] * 100, ha_li = km2[2] * 100, ha_ls = km2[3] * 100)
}))
co2_bio[, `:=`(tco2e = ha_evitados * EF[bioma] * (1 - v) * (1 - r),
               tco2e_li = ha_li * EF[bioma] * (1 - v) * (1 - r),
               tco2e_ls = ha_ls * EF[bioma] * (1 - v) * (1 - r))]
tot <- co2_bio[, lapply(.SD, sum), .SDcols = c("ha_evitados", "ha_li", "ha_ls",
                                               "tco2e", "tco2e_li", "tco2e_ls")]
print(co2_bio); print(tot)

# 2. Ano a ano, pelo estudo de eventos por bioma (para 2021-2022)
es <- mod$es_bio[ano >= 2018]
es <- area_alvo[es, on = "bioma"]
es[, `:=`(ha = -Estimate / 100 * area * 100,
          ha_li = -(Estimate + 1.96 * `Std. Error`) / 100 * area * 100,
          ha_ls = -(Estimate - 1.96 * `Std. Error`) / 100 * area * 100)]
anual <- es[, .(ha = sum(ha), ha_li = sum(ha_li), ha_ls = sum(ha_ls)), by = ano][order(ano)]
ha_2122 <- anual[ano %in% 2021:2022, lapply(.SD, sum), .SDcols = c("ha", "ha_li", "ha_ls")]

# 3. Linha de base histórica (estilo ART TREES) para MT — PRODES Amazônia Legal
cfg <- fromJSON("dados_brutos/config_loinames_prodes_legal_amazon.json", simplifyVector = FALSE)
uf_dic <- Filter(function(l) l$name == "uf", cfg$lois)[[1]]$loinames
gid_mt <- Filter(function(x) x$loiname == "Mato Grosso", uf_dic)[[1]]$gid
dat <- fromJSON("dados_brutos/data_prodes_legal_amazon.json", simplifyVector = FALSE)
mt_al <- rbindlist(lapply(dat$periods, function(pp) {
  f <- Filter(function(z) z$loi == 1 && z$loiname == gid_mt, pp$features)
  if (!length(f)) return(NULL)
  data.table(ano = pp$endDate$year, km2 = sum(sapply(f[[1]]$areas, `[[`, "area")))
}))[order(ano)][ano %between% c(2008, 2024)]
base_hist <- mt_al[ano %between% c(2013, 2017), mean(km2)]
mt_al[, `:=`(linha_base_km2 = fifelse(ano >= 2018, base_hist, NA_real_),
             reducao_hist_km2 = fifelse(ano >= 2018, base_hist - km2, NA_real_),
             abaixo_gatilho = km2 < 1788)]
fwrite(mt_al, "resultados/tabelas/tab9_mt_amazonia_legal_linha_base.csv")
red_hist_ha <- mt_al[ano >= 2018, sum(pmax(reducao_hist_km2, 0))] * 100

# Tabela de comparações
cmp <- data.table(
  referencia = c("Área evitada DDD 2018-2024 (ha), alto risco de MT",
                 "Emissões evitadas DDD 2018-2024 (tCO2e, após descontos)",
                 "Meta de resultados remunerados na fase 1 (tCO2e)",
                 "Área evitada DDD 2021-2022 (ha)",
                 "Desmatamento evitado divulgado pelo programa 2021-2022 (ha)",
                 "Redução sob linha de base histórica 2013-2017, 2018-2024 (ha, MT Amazônia Legal)"),
  valor = c(sprintf("%s [IC95: %s; %s]", format(round(tot$ha_evitados), big.mark = ".", decimal.mark = ","),
                    format(round(tot$ha_li), big.mark = ".", decimal.mark = ","), format(round(tot$ha_ls), big.mark = ".", decimal.mark = ",")),
            sprintf("%s [IC95: %s; %s]", format(round(tot$tco2e), big.mark = ".", decimal.mark = ","),
                    format(round(tot$tco2e_li), big.mark = ".", decimal.mark = ","), format(round(tot$tco2e_ls), big.mark = ".", decimal.mark = ",")),
            "10.091.830",
            sprintf("%s [IC95: %s; %s]", format(round(ha_2122$ha), big.mark = ".", decimal.mark = ","),
                    format(round(ha_2122$ha_li), big.mark = ".", decimal.mark = ","), format(round(ha_2122$ha_ls), big.mark = ".", decimal.mark = ",")),
            "160.000",
            format(round(red_hist_ha), big.mark = ".", decimal.mark = ",")))
print(cmp)
fwrite(cmp, "resultados/tabelas/tab10_co2_comparacoes.csv")
fwrite(co2_bio, "resultados/tabelas/tab10b_co2_por_bioma.csv")
fwrite(anual, "resultados/tabelas/tab10c_area_evitada_anual.csv")

# Figura: MT (Amazônia Legal), linha de base histórica e gatilho
png("resultados/figuras/fig3_mt_linha_base.png", width = 1800, height = 1000, res = 220)
par(mar = c(4, 4.5, 2.5, 1))
plot(mt_al$ano, mt_al$km2, type = "b", pch = 19, col = "#1b6b4a",
     ylim = c(0, max(mt_al$km2) * 1.05), xlab = "Ano PRODES", ylab = "Desmatamento (km²)",
     main = "MT — PRODES Amazônia Legal, linha de base e gatilho do REM", cex.main = 1)
abline(h = 1788, col = "#b2182b", lty = 2)
segments(2017.5, base_hist, 2024.5, base_hist, col = "#2166ac", lwd = 2)
abline(v = 2017.5, col = "grey50", lty = 3)
legend("topleft", c("Desmatamento observado", "Gatilho (1.788 km²)",
                    "Linha de base histórica 2013-2017"),
       col = c("#1b6b4a", "#b2182b", "#2166ac"), lty = c(1, 2, 1), pch = c(19, NA, NA),
       bty = "n", cex = .8)
dev.off()

saveRDS(list(co2_bio = co2_bio, tot = tot, anual = anual, ha_2122 = ha_2122,
             mt_al = mt_al, base_hist = base_hist, red_hist_ha = red_hist_ha, cmp = cmp,
             EF = EF, r = r, v = v), "resultados/co2.rds")
