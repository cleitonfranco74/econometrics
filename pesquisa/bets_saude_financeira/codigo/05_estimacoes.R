# =============================================================================
# 05 - Estimações: bloqueio de bets ilegais (out/2024) e saúde financeira
#
# Exposição: DigYouth (eq. 2), pré-determinada em 2022 — a medida primária do
# artigo (Pix para CNAE 92 por município, eq. 1) não é pública.
#
#   1. Balanceamento: DigYouth x características municipais
#   2. DiD contínuo TWFE (eq. 3) — poupança, depósitos, crédito, ISS
#      com (a) EF município + mês; (b) + UF x mês; (c) + mês x covariáveis
#   3. Estudo de evento (eq. 4), k = -21..+14, ref. set/2024
#   4. Dois eventos: bloqueio (out-dez/2024) x vigência plena (2025) (eq. 6)
#   5. Dose-resposta: quartis de DigYouth x pós; CGBS (contdid)
#   6. Heterogeneidade (H3 renda, H4 jovens) e robustez (pop 20-500 mil,
#      componentes de DigYouth, placebo out/2023)
#
# Execute de dentro de codigo/:  Rscript 05_estimacoes.R
# =============================================================================
suppressPackageStartupMessages({
  library(data.table); library(fixest); library(ggplot2)
})
invisible(Sys.setlocale("LC_ALL", "C.UTF-8"))
set.seed(20241001)
RES <- "../resultados"; dir.create(RES, showWarnings = FALSE)
sink(file.path(RES, "saida_estimacoes.txt"), split = TRUE)
cat("Estimações — bets e saúde financeira —", format(Sys.time()), "\n")
setFixest_notes(FALSE)
setFixest_dict(c(post_dz = "DigYouth(z) x Pós", block_dz = "DigYouth(z) x Bloqueio (out-dez/24)",
                 legal_dz = "DigYouth(z) x Vigência (2025)",
                 ln_poupanca_pc = "ln poupança pc", ln_dep_vista_pc = "ln dep. à vista pc",
                 ln_dep_prazo_pc = "ln dep. a prazo pc", ln_credito_pc = "ln crédito pc",
                 asinh_iss_pc = "asinh ISS pc"))

p <- fread("../dados/painel_bets_mensal.csv")
p[, `:=`(post_dz = post * digyouth_z, block_dz = block * digyouth_z,
         legal_dz = legal * digyouth_z)]
E <- p[balanceado == 1]                      # municípios com agência nos 36 meses
cat("\nMunicípios no painel ESTBAN balanceado:", uniqueN(E$cod_ibge),
    "| observações:", nrow(E), "\n")
Yb <- c("ln_poupanca_pc", "ln_dep_vista_pc", "ln_dep_prazo_pc", "ln_credito_pc")

# -----------------------------------------------------------------------------
cat("\n================ 1. Balanceamento: DigYouth vs. características ================\n")
c1 <- unique(p[, .(cod_ibge, digyouth_z, ln_pib_pc_2021, ln_pop_2022, sh_jovens_18_35,
                   banda_larga_100dom)])
print(round(cor(c1[, -1], use = "complete.obs"), 2))
pre <- E[rel < 0, .(g_poup = mean(ln_poupanca_pc[rel >= -3]) - mean(ln_poupanca_pc[rel <= -19])),
         by = cod_ibge][c1, on = "cod_ibge", nomatch = 0]
print(etable(feols(g_poup ~ digyouth_z, pre), feols(g_poup ~ digyouth_z + ln_pib_pc_2021 + ln_pop_2022, pre),
             title = "Crescimento pré (jan-mar/23 a jul-set/24) da poupança vs. DigYouth"))

# -----------------------------------------------------------------------------
cat("\n================ 2. DiD contínuo (eq. 3) ================\n")
m_a <- feols(.[Yb] ~ post_dz | cod_ibge + anomes, E, cluster = ~cod_ibge)
m_b <- feols(.[Yb] ~ post_dz | cod_ibge + uf^anomes, E, cluster = ~cod_ibge)
m_c <- feols(.[Yb] ~ post_dz + ln_agencias | cod_ibge + uf^anomes +
               anomes[ln_pib_pc_2021, ln_pop_2022], E, cluster = ~cod_ibge)
etable(m_a, title = "(a) EF município + mês")
etable(m_b, title = "(b) EF município + UF x mês")
etable(m_c, title = "(c) + mês x (ln PIB pc, ln pop) + ln agências")
tab2 <- rbindlist(lapply(list(a = m_a, b = m_b, c = m_c), function(ms)
  rbindlist(lapply(ms, function(m) data.table(y = as.character(m$fml[[2]]),
    coef = coef(m)["post_dz"], ep = se(m)["post_dz"], p = pvalue(m)["post_dz"], n = nobs(m))))),
  idcol = "especificacao")
fwrite(tab2, file.path(RES, "tab2_did_continuo.csv"))

# ISS (todos os municípios com RREO; não depende de agência)
I <- p[is.finite(asinh_iss_pc) & !is.na(digyouth_z)]
I <- I[, if (.N == 36) .SD, by = cod_ibge]
if (nrow(I) > 0) {
  iss_m <- feols(asinh_iss_pc ~ post_dz | cod_ibge + csw(anomes, uf^anomes,
                   uf^anomes + anomes[ln_pib_pc_2021, ln_pop_2022]), I, cluster = ~cod_ibge)
  print(etable(iss_m, title = sprintf("H6: ISS per capita (%d municípios)", uniqueN(I$cod_ibge))))
  iss_es <- feols(asinh_iss_pc ~ i(rel, digyouth_z, ref = -1) | cod_ibge + uf^anomes +
                    anomes[ln_pib_pc_2021, ln_pop_2022], I, cluster = ~cod_ibge)
  print(etable(iss_es, title = "H6: estudo de evento do ISS"))
  png(file.path(RES, "fig3b_evento_iss.png"), width = 1400, height = 700, res = 150)
  iplot(iss_es, main = "asinh ISS per capita", xlab = "Meses em relação a out/2024")
  dev.off()
} else cat("ISS ainda não disponível (rode 02_iss_siconfi.py).\n")

# -----------------------------------------------------------------------------
cat("\n================ 3. Estudo de evento (eq. 4), ref. set/2024 ================\n")
es <- feols(.[Yb] ~ i(rel, digyouth_z, ref = -1) | cod_ibge + uf^anomes, E, cluster = ~cod_ibge)
es_c <- feols(.[Yb] ~ i(rel, digyouth_z, ref = -1) | cod_ibge + uf^anomes +
                anomes[ln_pib_pc_2021, ln_pop_2022], E, cluster = ~cod_ibge)
nm <- c("Poupança", "Dep. à vista", "Dep. a prazo", "Crédito")
png(file.path(RES, "fig3_evento.png"), width = 2000, height = 1300, res = 150)
par(mfrow = c(2, 2))
for (k in 1:4) {
  iplot(list(es[[k]], es_c[[k]]), main = paste("ln", nm[k], "per capita"),
        xlab = "Meses em relação a out/2024", ylab = "Coef. DigYouth(z) x mês")
  legend("topleft", c("UF x mês", "+ mês x covariáveis"), col = 1:2, pch = c(20, 17), bty = "n", cex = .8)
}
dev.off()
# teste conjunto das pré-tendências
for (k in 1:4) {
  pre_coefs <- grep("rel::-([2-9]|1[0-9]|2[0-1]):", names(coef(es_c[[k]])), value = TRUE)
  w <- wald(es_c[[k]], keep = paste0("^", gsub("([\\[\\]\\(\\)\\.\\^\\$\\|\\?\\*\\+\\{\\}])", "\\\\\\1", pre_coefs), "$"), print = FALSE)
  cat(sprintf("%-14s Wald pré-tendências (com covariáveis): F = %.2f, p = %.3f\n", nm[k], w$stat, w$p))
}

# -----------------------------------------------------------------------------
cat("\n================ 4. Dois eventos (eq. 6): bloqueio x vigência ================\n")
m6 <- feols(.[Yb] ~ block_dz + legal_dz | cod_ibge + uf^anomes +
              anomes[ln_pib_pc_2021, ln_pop_2022], E, cluster = ~cod_ibge)
etable(m6)
tab4 <- rbindlist(lapply(m6, function(m) data.table(y = as.character(m$fml[[2]]),
  b1_bloqueio = coef(m)["block_dz"], ep1 = se(m)["block_dz"],
  b2_vigencia = coef(m)["legal_dz"], ep2 = se(m)["legal_dz"])))
fwrite(tab4, file.path(RES, "tab4_dois_eventos.csv"))

# -----------------------------------------------------------------------------
cat("\n================ 5. Dose-resposta ================\n")
E[, q := factor(digyouth_q)]
mq <- feols(.[Yb] ~ i(q, post, ref = 1) | cod_ibge + uf^anomes +
              anomes[ln_pib_pc_2021, ln_pop_2022], E, cluster = ~cod_ibge)
etable(mq, title = "Quartis de DigYouth x Pós (ref.: 1º quartil)")

cat("\nCallaway, Goodman-Bacon e Sant'Anna (contdid): dose-resposta\n")
cat("Dose = DigYouth; grupo de comparação (dose 0) = 1º decil de DigYouth;\n",
    "painel trimestral (média dos meses), tratamento no 8º trimestre (out-dez/2024).\n",
    "Sem covariáveis (o pacote ainda não as aceita): comparar com a seção 2(a).\n")
cgbs <- list()
if (requireNamespace("contdid", quietly = TRUE)) {
  for (y in c("ln_poupanca_pc", "ln_dep_vista_pc", "ln_credito_pc")) {
    B <- E[, .(Y = mean(get(y))), by = .(cod_ibge, time_period = as.numeric((periodo - 1) %/% 3 + 1),
                                         digyouth, digyouth_dec)]
    B <- B[, if (all(is.finite(Y))) .SD, by = cod_ibge]   # descarta poupança/crédito = 0
    B[, `:=`(id = as.integer(factor(cod_ibge)), G = fifelse(digyouth_dec == 1, 0, 8))]
    B[, D := fifelse(G == 0, 0, digyouth)]
    df <- as.data.frame(B[, .(id, G, D, time_period, Y)])
    arg <- list(yname = "Y", tname = "time_period", idname = "id", dname = "D", gname = "G",
                data = df, target_parameter = "level", treatment_type = "continuous",
                control_group = "nevertreated", biters = 500, cband = FALSE,
                num_knots = 1, degree = 3)
    cd <- tryCatch(do.call(contdid::cont_did, c(arg, aggregation = "dose")),
                   error = function(e) { cat(y, "falhou:", conditionMessage(e), "\n"); NULL })
    ce <- tryCatch(do.call(contdid::cont_did, c(arg, aggregation = "eventstudy")),
                   error = function(e) NULL)
    if (!is.null(cd)) {
      cat("\n---", y, "---\n"); print(summary(cd))
      cgbs[[y]] <- data.table(y = y, att = cd$overall_att, ep_att = cd$overall_att_se,
                              acrt = cd$overall_acrt, ep_acrt = cd$overall_acrt_se)
      pl <- tryCatch(plot(cd, type = "att") + ggtitle(paste("CGBS — ATT(d):", y)), error = function(e) NULL)
      if (!is.null(pl)) ggsave(file.path(RES, paste0("fig5_cgbs_dose_", y, ".png")), pl,
                               width = 8, height = 4.5, dpi = 150)
    }
    if (!is.null(ce)) {
      cat("Estudo de evento CGBS (ATT por trimestre relativo):\n"); print(summary(ce))
      pl <- tryCatch(plot(ce) + ggtitle(paste("CGBS — evento:", y)), error = function(e) NULL)
      if (!is.null(pl)) ggsave(file.path(RES, paste0("fig5_cgbs_evento_", y, ".png")), pl,
                               width = 8, height = 4.5, dpi = 150)
    }
  }
  if (length(cgbs)) fwrite(rbindlist(cgbs, fill = TRUE), file.path(RES, "tab5_cgbs.csv"))
}

# -----------------------------------------------------------------------------
cat("\n================ 6. Heterogeneidade e robustez ================\n")
het <- feols(.[Yb[c(1, 2)]] ~ post_dz + post_dz:baixa_renda + post_dz:mais_jovens |
               cod_ibge + uf^anomes + anomes[ln_pib_pc_2021, ln_pop_2022], E, cluster = ~cod_ibge)
etable(het, title = "H3 (baixa renda) e H4 (mais jovens)")

r1 <- feols(.[Yb[c(1, 2)]] ~ post_dz | cod_ibge + uf^anomes + anomes[ln_pib_pc_2021, ln_pop_2022],
            E[pop_20k_500k == 1], cluster = ~cod_ibge)
etable(r1, title = "Robustez (a): população 20-500 mil")

E[, `:=`(post_hz = post * sh_homens_18_35_z, post_bz = post * banda_larga_100dom_z)]
r2 <- feols(.[Yb[c(1, 2)]] ~ post_hz + post_bz | cod_ibge + uf^anomes +
              anomes[ln_pib_pc_2021, ln_pop_2022], E, cluster = ~cod_ibge)
etable(r2, title = "Componentes de DigYouth: homens 18-35 e banda larga, separados")

P <- E[rel < 0]
P[, post_fake := as.integer(anomes >= 202310) * digyouth_z]
r3 <- feols(.[Yb] ~ post_fake | cod_ibge + uf^anomes + anomes[ln_pib_pc_2021, ln_pop_2022],
            P, cluster = ~cod_ibge)
etable(r3, title = "Placebo: 'bloqueio' fictício em out/2023 (só período pré)")

cat("\nNão estimado: H2 (inadimplência PF por município — o SCR só é público por UF);",
    "HonestDiD (pacote não instalável neste ambiente).\n")
sink()
