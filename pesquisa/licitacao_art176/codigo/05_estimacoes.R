# =============================================================================
# 05 - Estimações: licitação eletrônica e o art. 176 da Lei 14.133/2021 (PR)
#
#   0. Primeiro estágio (teste de viabilidade da seção 6 do projeto)
#   A. DiD do corte legal (intenção de tratar): obrigado x pós, painel trimestral
#      + estudo de evento anual + robustez de amostras + PPML para contagens
#   B. Diferenças-em-descontinuidades em 20 mil hab. (Grembi et al., 2016)
#   C. DiD pela adoção efetiva (Elet >= 0,5; Callaway e Sant'Anna, 2021)
#      + Sun e Abraham (2021) + placebo interno (H5) + heterogeneidade
#
# Execute de dentro de codigo/:  Rscript 05_estimacoes.R
# Resultados em ../resultados/
# =============================================================================
suppressPackageStartupMessages({
  library(data.table); library(fixest); library(did)
  library(rdrobust); library(ggplot2)
})
set.seed(20240101)
invisible(Sys.setlocale("LC_ALL", "C.UTF-8"))  # acentos nos gráficos
RES <- "../resultados"; dir.create(RES, showWarnings = FALSE)
sink(file.path(RES, "saida_estimacoes.txt"), split = TRUE)
cat("Estimações art. 176 —", format(Sys.time()), "\n")

tri <- fread("../dados/painel_trimestral.csv")
ano <- fread("../dados/painel_anual.csv")
setFixest_notes(FALSE)
dict <- c(obrig_pos = "Obrigado x Pós", share_diretas = "Part. diretas (nº)",
          share_diretas_valor = "Part. diretas (valor)",
          asinh_n_processos = "asinh(nº processos)",
          asinh_n_competitivos = "asinh(nº competitivos)",
          asinh_n_diretas = "asinh(nº diretas)", elet = "Elet")
setFixest_dict(dict)
tema <- theme_minimal(base_size = 12)
salva <- function(p, nome) ggsave(file.path(RES, nome), p, width = 8, height = 4.5, dpi = 150)

# -----------------------------------------------------------------------------
# 0. PRIMEIRO ESTÁGIO
# -----------------------------------------------------------------------------
cat("\n================ 0. PRIMEIRO ESTÁGIO ================\n")
fe <- fread("../dados/primeiro_estagio_faixas.csv")
print(fe)

pe <- ano[ano >= 2021 & !is.na(elet)]
g0 <- pe[, .(elet = mean(elet), pct50 = mean(elet >= .5)), by = .(ano, obrigado)]
p <- ggplot(g0, aes(ano, pct50, colour = factor(obrigado, 0:1, c("Até 20 mil (art. 176)", "Acima de 20 mil")))) +
  geom_line(linewidth = 1) + geom_point(size = 2) +
  geom_vline(xintercept = 2023.5, linetype = 2) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = NULL, y = "% municípios com Elet >= 0,5", colour = NULL,
       title = "Adoção da forma eletrônica (PNCP) por grupo do art. 176") + tema +
  theme(legend.position = "bottom")
salva(p, "fig0_primeiro_estagio.png")

fs_did <- feols(elet ~ obrig_pos | cod_ibge + ano, pe, cluster = ~cod_ibge)
fs_es  <- feols(elet ~ i(ano, obrigado, ref = 2023) | cod_ibge + ano, pe, cluster = ~cod_ibge)
etable(fs_did, fs_es, title = "Primeiro estágio: Elet ~ obrigado x pós")

cat("\nRD do primeiro estágio (Elet 2024 e 2025) em 20 mil hab.:\n")
fs_rd <- rbindlist(lapply(c(2024, 2025), function(a) {
  d <- ano[ano == a & !is.na(elet)]
  r <- rdrobust(d$elet, d$pop_2022_censo, c = 20000)
  data.table(ano = a, coef = r$coef[1], ep = r$se[3], p_robusto = r$pv[3],
             h = r$bws[1, 1], n_esq = r$N_h[1], n_dir = r$N_h[2])
}))
print(fs_rd); fwrite(fs_rd, file.path(RES, "tab0_rd_primeiro_estagio.csv"))

# -----------------------------------------------------------------------------
# A. DiD DO CORTE LEGAL (ITT) — painel trimestral, EF de município e trimestre
# -----------------------------------------------------------------------------
cat("\n================ A. DiD do corte legal (ITT) ================\n")
Y <- c("share_diretas", "share_diretas_valor", "asinh_n_processos",
       "asinh_n_competitivos", "asinh_n_diretas")
amostras <- list(
  completa = tri,
  sem_entorno_ctba = tri[entorno_curitiba == 0],
  pop_5k_50k = tri[pop_2022_censo >= 5000 & pop_2022_censo <= 50000],
  pop_10k_30k = tri[pop_2022_censo >= 10000 & pop_2022_censo <= 30000])
itt <- rbindlist(lapply(names(amostras), function(nm) {
  rbindlist(lapply(Y, function(y) {
    m <- feols(as.formula(paste(y, "~ obrig_pos | cod_ibge + trimestre")),
               amostras[[nm]], cluster = ~cod_ibge)
    data.table(amostra = nm, y = y, coef = coef(m)[1], ep = se(m)[1],
               p = pvalue(m)[1], n = nobs(m),
               municipios = uniqueN(amostras[[nm]]$cod_ibge))
  }))
}))
print(itt, digits = 3); fwrite(itt, file.path(RES, "tabA1_itt_did.csv"))

# Robustez: população de 2021 no lugar do Censo 2022
tri[, obrig_pos21 := obrigado_pop2021 * pos]
rob21 <- feols(c(share_diretas, asinh_n_processos, asinh_n_competitivos) ~ obrig_pos21 |
                 cod_ibge + trimestre, tri, cluster = ~cod_ibge)
etable(rob21, title = "ITT com população estimada de 2021")

# Tendências específicas por covariável (pós x covariáveis pré-tratamento)
tri[, `:=`(pos_lpop = pos * ln_pop_2019, pos_lpib = pos * ln_pib_pc_2019,
           pos_lrec = pos * ln_rec_propria_pc_2019, pos_pes = pos * pessoal_rc_2019,
           pos_fpm = pos * dep_fpm_2019, pos_dist = pos * dist_curitiba_km / 100)]
robX <- feols(c(share_diretas, asinh_n_processos, asinh_n_competitivos) ~ obrig_pos +
                pos_lpop + pos_lpib + pos_lrec + pos_pes + pos_fpm + pos_dist |
                cod_ibge + trimestre, tri, cluster = ~cod_ibge)
etable(robX, keep = "Obrigado", title = "ITT com pós x covariáveis de 2019")

# PPML (Santos Silva e Tenreyro, 2006) para contagens
ppml <- fepois(c(n_competitivos, n_pregoes, n_diretas, n_processos) ~ obrig_pos |
                 cod_ibge + trimestre, tri, cluster = ~cod_ibge)
etable(ppml, title = "PPML: contagens de processos (coef. = variação log)")

# Estudo de evento anual (ref. 2020); 2021 = só 1º trimestre; 2026 = 1º trim.
tri[, ano_ev := ano]
es <- feols(c(share_diretas, asinh_n_processos, asinh_n_competitivos) ~
              i(ano_ev, obrigado, ref = 2020) | cod_ibge + trimestre, tri, cluster = ~cod_ibge)
etable(es, title = "Estudo de evento (obrigado x ano), ref. 2020")
nomes_es <- c("Part. diretas (nº)", "asinh(nº processos)", "asinh(nº competitivos)")
png(file.path(RES, "figA_evento_itt.png"), width = 1800, height = 600, res = 150)
par(mfrow = c(1, 3))
for (k in 1:3) iplot(es[[k]], main = nomes_es[k], xlab = "Ano (2021 e 2026: só 1º trimestre)")
dev.off()

# -----------------------------------------------------------------------------
# B. DIFERENÇAS-EM-DESCONTINUIDADES (ΔY = média pós - média pré)
# -----------------------------------------------------------------------------
cat("\n================ B. Diferenças-em-descontinuidades ================\n")
dd <- tri[, .(d_share = mean(share_diretas[pos == 1], na.rm = TRUE) -
                mean(share_diretas[pos == 0], na.rm = TRUE),
              d_share_valor = mean(share_diretas_valor[pos == 1], na.rm = TRUE) -
                mean(share_diretas_valor[pos == 0], na.rm = TRUE),
              d_asinh_proc = mean(asinh_n_processos[pos == 1]) - mean(asinh_n_processos[pos == 0]),
              d_asinh_comp = mean(asinh_n_competitivos[pos == 1]) - mean(asinh_n_competitivos[pos == 0])),
          by = .(cod_ibge, pop = pop_2022_censo)]
rd_tab <- rbindlist(lapply(c("d_share", "d_share_valor", "d_asinh_proc", "d_asinh_comp"), function(v) {
  rbindlist(lapply(list(list(p = 1, h = NULL), list(p = 2, h = NULL), list(p = 1, h = 2900)), function(s) {
    ok <- is.finite(dd[[v]])
    r <- if (is.null(s$h)) rdrobust(dd[[v]][ok], dd$pop[ok], c = 20000, p = s$p) else
      rdrobust(dd[[v]][ok], dd$pop[ok], c = 20000, p = s$p, h = s$h)
    data.table(y = v, polinomio = s$p, h = round(r$bws[1, 1]), coef = r$coef[1],
               ep_robusto = r$se[3], p_robusto = r$pv[3], n_esq = r$N_h[1], n_dir = r$N_h[2])
  }))
}))
print(rd_tab, digits = 3); fwrite(rd_tab, file.path(RES, "tabB_diff_in_disc.csv"))
cat("Nota: com h = 2.900 há poucos municípios de cada lado; leitura apenas indicativa.\n")

# Balanço de covariáveis pré-tratamento no corte
cov1 <- unique(tri[, .(cod_ibge, pop_2022_censo, ln_pib_pc_2019, ln_rec_propria_pc_2019,
                       pessoal_rc_2019, dep_fpm_2019, dist_curitiba_km)])
bal <- rbindlist(lapply(c("ln_pib_pc_2019", "ln_rec_propria_pc_2019", "pessoal_rc_2019",
                          "dep_fpm_2019", "dist_curitiba_km"), function(v) {
  ok <- is.finite(cov1[[v]])
  r <- rdrobust(cov1[[v]][ok], cov1$pop_2022_censo[ok], c = 20000)
  data.table(covariavel = v, coef = r$coef[1], p_robusto = r$pv[3])
}))
print(bal, digits = 3); fwrite(bal, file.path(RES, "tabB_balanco_covariaveis.csv"))
png(file.path(RES, "figB_rdplot_share_diretas.png"), width = 1200, height = 800, res = 150)
ok <- is.finite(dd$d_share) & dd$pop < 60000
rdplot(dd$d_share[ok], dd$pop[ok], c = 20000, title = "Δ participação de contratações diretas",
       x.label = "População (Censo 2022)", y.label = "Δ (pós - pré)")
dev.off()

# -----------------------------------------------------------------------------
# C. DiD PELA ADOÇÃO EFETIVA (Callaway e Sant'Anna) — painel anual
#    Desfechos só existem em 2018, 2019, 2020 e 2025 (anos completos do Mural).
#    Logo, todo município que adotou entre 2022 e 2025 aparece tratado pela
#    primeira vez em 2025: há UMA coorte observável (g = 2025) e o controle são
#    os que adotam em 2026 ou nunca (ainda não tratados em 2025).
# -----------------------------------------------------------------------------
cat("\n================ C. DiD pela adoção efetiva (Elet >= 0,5) ================\n")
an <- ano[ano %in% c(2018, 2019, 2020, 2025)]
an[, t := match(ano, c(2018, 2019, 2020, 2025))]
an[, `:=`(asinh_n_processos = asinh(n_processos), asinh_n_competitivos = asinh(n_competitivos),
          asinh_n_diretas = asinh(n_diretas))]
roda_cs <- function(dat, gvar, y, rot, xf = ~1) {
  dat <- copy(dat)
  dat[, gcs := fifelse(get(gvar) > 0 & get(gvar) <= 2025, 4L, 0L)]
  dat <- dat[is.finite(get(y))]
  dat <- dat[, if (.N == 4) .SD, by = cod_ibge]           # painel balanceado
  r <- tryCatch(att_gt(yname = y, tname = "t", idname = "cod_ibge", gname = "gcs",
                       xformla = xf, data = as.data.frame(dat), control_group = "nevertreated",
                       est_method = "dr", bstrap = TRUE, cband = FALSE, base_period = "universal"),
                error = function(e) NULL)
  if (is.null(r)) return(data.table(rotulo = rot, y = y, att = NA_real_))
  s <- aggte(r, type = "simple")
  pre <- data.table(t = r$t, att = r$att, se = r$se)[t < 4]
  data.table(rotulo = rot, y = y, att = s$overall.att, ep = s$overall.se,
             pre_2018 = pre[t == 1, att], pre_2019 = pre[t == 2, att],
             tratados = sum(dat[t == 1, gcs] == 4), controles = sum(dat[t == 1, gcs] == 0))
}
Yc <- c("share_diretas", "share_diretas_valor", "asinh_n_processos",
        "asinh_n_competitivos", "asinh_n_diretas")
X <- ~ ln_pop_2019 + ln_pib_pc_2019 + ln_rec_propria_pc_2019 + pessoal_rc_2019 + dep_fpm_2019
cs <- rbindlist(c(
  lapply(Yc, function(y) roda_cs(an, "G_elet50", y, "Elet50, sem covariáveis")),
  lapply(Yc, function(y) roda_cs(an, "G_elet50", y, "Elet50, com covariáveis (DR)", X)),
  lapply(Yc, function(y) roda_cs(an, "G_elet25", y, "Elet25")),
  lapply(Yc, function(y) roda_cs(an, "G_elet75", y, "Elet75")),
  # adoção na data da obrigação (2024) vs. ainda não/nunca: exclui adotantes voluntários precoces
  lapply(Yc, function(y) roda_cs(an[!(G_elet50 %in% c(2022, 2023))], "G_elet50", y, "Só coorte 2024-25 (exclui 2022-23)")),
  # heterogeneidade
  lapply(Yc, function(y) roda_cs(an[obrigado == 0], "G_elet50", y, "Het.: até 20 mil")),
  lapply(Yc, function(y) roda_cs(an[obrigado == 1], "G_elet50", y, "Het.: acima de 20 mil")),
  lapply(Yc, function(y) roda_cs(an[baixa_capacidade == 1], "G_elet50", y, "Het.: baixa capacidade fiscal")),
  lapply(Yc, function(y) roda_cs(an[baixa_capacidade == 0], "G_elet50", y, "Het.: alta capacidade fiscal"))
), fill = TRUE)
print(cs, digits = 3); fwrite(cs, file.path(RES, "tabC_callaway_santanna.csv"))

# Sun e Abraham (fixest::sunab), mesma estrutura de coortes
an[, coorte_sa := fifelse(G_elet50 > 0 & G_elet50 <= 2025, 2025L, 10000L)]
sa <- feols(c(share_diretas, asinh_n_processos, asinh_n_competitivos) ~
              sunab(coorte_sa, ano, ref.p = -5) | cod_ibge + ano, an, cluster = ~cod_ibge)
etable(sa, title = "Sun e Abraham (ref.: 2020)")

# TWFE de referência (anual)
tw <- feols(c(share_diretas, asinh_n_processos, asinh_n_competitivos) ~ D_elet50 |
              cod_ibge + ano, an, cluster = ~cod_ibge)
etable(tw, title = "TWFE de referência (D_elet50)")
cat("Goodman-Bacon: com uma única coorte observável (2025) o TWFE é um 2x2 e a",
    "decomposição é trivial (100% do peso em tratados x nunca/ainda não tratados).\n")

# H5 — placebo interno: municípios que já eram eletrônicos em 2023 (antes da obrigação)
cat("\nH5 (placebo interno): ITT entre municípios já eletrônicos em 2023\n")
h5 <- feols(c(share_diretas, asinh_n_processos, asinh_n_competitivos) ~ obrig_pos |
              cod_ibge + trimestre, tri[ja_eletronico_2023 == 1], cluster = ~cod_ibge)
etable(h5)

cat("\nHonestDiD (Rambachan e Roth): não executado — o pacote não pôde ser instalado",
    "neste ambiente; e com só 3 períodos pré anuais e uma coorte a análise teria pouco poder.\n")
sink()
