# =============================================================================
# 03_estimacao.R — triplas diferenças (DDD), estudo de eventos e robustez
#
# Modelo principal:
#   y_ist = β (MT_s × Alto_i × Pós_t) + α_i + δ_{s,bioma,t} + λ_{faixa,bioma,t} + ε
#   y = desmatamento anual em % da área do município (PRODES)
# =============================================================================

invisible(Sys.setlocale("LC_ALL", "C.UTF-8"))
suppressPackageStartupMessages({ library(data.table); library(fixest) })
setFixest_notes(FALSE)
dir.create("resultados/tabelas", recursive = TRUE, showWarnings = FALSE)
dir.create("resultados/figuras", recursive = TRUE, showWarnings = FALSE)

p_all <- fread("dados/painel_rem_mt.csv")
p     <- p_all[uf != "TO"]                       # amostra principal (sem Tocantins)

# Efeitos fixos (iguais em todas as especificações):
#   id          = município × bioma                       (α_i)
#   uf^bioma^ano = choques comuns a um estado em um ano    (δ_st)
#   alto^bioma^ano = choques que atingem mais o alto risco (λ_gt)
fe <- "id + uf^bioma^ano + alto^bioma^ano"
vc <- ~cod_ibge                                   # cluster: município

ddd <- function(dados, y = "y", trat = "ddd", fe_ = fe, extra = "", f = feols, ...) {
  fml <- as.formula(sprintf("%s ~ %s %s | %s", y, trat, extra, fe_))
  f(fml, data = dados, cluster = vc, ...)
}

# ---------------------------------------------------------------------------
# 1. Média das 8 células (tabela do projeto) e estimador DDD "na mão"
# ---------------------------------------------------------------------------
cel <- p[, .(y = mean(y)), by = .(grupo = fifelse(mt == 1, "MT", "Controles"),
                                  risco = fifelse(alto == 1, "alto", "baixo"),
                                  periodo = fifelse(pos == 1, "depois", "antes"))]
cel <- dcast(cel, grupo + risco ~ periodo, value.var = "y")
cel[, dif := depois - antes]
setorder(cel, -grupo, risco)
ddd_mao <- (cel[grupo == "MT" & risco == "alto", dif] - cel[grupo == "MT" & risco == "baixo", dif]) -
           (cel[grupo == "Controles" & risco == "alto", dif] - cel[grupo == "Controles" & risco == "baixo", dif])
fwrite(cel, "resultados/tabelas/tab1_celulas_ddd.csv")
cat("\nDDD com médias simples (sem efeitos fixos):", round(ddd_mao, 4), "\n")

# ---------------------------------------------------------------------------
# 2. Especificação principal e variações do resultado
# ---------------------------------------------------------------------------
m_ddd     <- ddd(p)
m_did     <- feols(y ~ mt:pos | id + bioma^ano, data = p[alto == 1], cluster = vc) # DiD simples (só alto risco: MT x controles)
m_cov     <- ddd(p, extra = "+ i(ano, bov_ini, ref = 2017) + i(ano, soja_ini, ref = 2017)")
m_asinh   <- ddd(p, y = "asinh_km2")
m_ppml    <- ddd(p, y = "km2", f = fepois)

etable(m_did, m_ddd, m_cov, m_asinh, m_ppml,
       keep = c("%mt:pos", "%^ddd$"),
       headers = c("DiD (alto risco)", "DDD", "DDD + cov.", "DDD asinh(km²)", "DDD PPML"),
       file = "resultados/tabelas/tab2_principal.tex", replace = TRUE)
tab2 <- etable(m_did, m_ddd, m_cov, m_asinh, m_ppml, keep = c("%mt:pos", "%^ddd$"),
               headers = c("DiD (alto risco)", "DDD", "DDD + cov.", "DDD asinh(km²)", "DDD PPML"))
print(tab2)
fwrite(as.data.table(tab2, keep.rownames = TRUE), "resultados/tabelas/tab2_principal.csv")

# média pré-programa do grupo tratado (para ler o efeito em %)
media_pre <- p[mt == 1 & alto == 1 & pos == 0, mean(y)]

# ---------------------------------------------------------------------------
# 3. Estudo de eventos (ano-base 2017)
# ---------------------------------------------------------------------------
p[, mt_alto := mt * alto]
es <- feols(as.formula(sprintf("y ~ i(ano, mt_alto, ref = 2017) | %s", fe)),
            data = p, cluster = vc)
es_tab <- as.data.table(coeftable(es), keep.rownames = "termo")
es_tab[, ano := as.integer(gsub("\\D", "", sub(":mt_alto", "", termo)))]
es_tab <- rbind(es_tab, data.table(termo = "ref", ano = 2017, Estimate = 0,
                                   `Std. Error` = 0), fill = TRUE)
setorder(es_tab, ano)
es_tab[, `:=`(li = Estimate - 1.96 * `Std. Error`, ls = Estimate + 1.96 * `Std. Error`)]
fwrite(es_tab, "resultados/tabelas/tab3_estudo_eventos.csv")
pre_teste <- wald(es, keep = "ano::201[0-6]", print = FALSE)
cat("\nTeste conjunto de pré-tendência (2010-2016): F =", round(pre_teste$stat, 2),
    " p =", round(pre_teste$p, 3), "\n")

# por bioma
es_bio <- lapply(c("Amazonia", "Cerrado"), function(b) {
  m <- feols(as.formula(sprintf("y ~ i(ano, mt_alto, ref = 2017) | %s", fe)),
             data = p[bioma == b], cluster = vc)
  d <- as.data.table(coeftable(m), keep.rownames = "termo")
  d[, `:=`(ano = as.integer(gsub("\\D", "", sub(":mt_alto", "", termo))), bioma = b)]
  rbind(d, data.table(ano = 2017L, Estimate = 0, `Std. Error` = 0, bioma = b), fill = TRUE)
})
es_bio <- rbindlist(es_bio)
fwrite(es_bio, "resultados/tabelas/tab3b_estudo_eventos_bioma.csv")

png("resultados/figuras/fig1b_estudo_eventos_bioma.png", width = 2000, height = 900, res = 220)
par(mfrow = c(1, 2), mar = c(4.5, 4.5, 2.5, 1))
for (b in c("Amazonia", "Cerrado")) {
  d <- es_bio[bioma == b][order(ano)]
  li <- d$Estimate - 1.96 * d$`Std. Error`; ls <- d$Estimate + 1.96 * d$`Std. Error`
  plot(d$ano, d$Estimate, ylim = c(-.4, .5), xlim = c(2010, 2024), pch = 19,
       col = "#1b6b4a", xlab = "Ano PRODES", ylab = "p.p. da área municipal",
       main = ifelse(b == "Amazonia", "Amazônia", "Cerrado"), cex.main = 1)
  ok <- d$`Std. Error` > 0
  arrows(d$ano[ok], li[ok], d$ano[ok], ls[ok], angle = 90, code = 3, length = .03, col = "#1b6b4a")
  abline(h = 0, lty = 2); abline(v = 2017.5, col = "grey50", lty = 3)
}
dev.off()

png("resultados/figuras/fig1_estudo_eventos.png", width = 1800, height = 1050, res = 220)
par(mar = c(4.5, 5.5, 2.5, 1))
plot(es_tab$ano, es_tab$Estimate, ylim = range(c(es_tab$li, es_tab$ls)), pch = 19,
     col = "#1b6b4a", xlab = "Ano PRODES (ago/t-1 a jul/t)",
     ylab = "Efeito sobre o desmatamento\n(p.p. da área municipal)", xaxt = "n",
     main = "Estudo de eventos — MT × alto risco (ano-base 2017)", cex.main = 1)
axis(1, at = 2010:2024, las = 2, cex.axis = .8)
arrows(es_tab$ano, es_tab$li, es_tab$ano, es_tab$ls, angle = 90, code = 3,
       length = .03, col = "#1b6b4a")
abline(h = 0, lty = 2); abline(v = 2017.5, col = "grey50", lty = 3)
text(2017.6, max(es_tab$ls), "início do REM MT", adj = 0, cex = .75, col = "grey30")
dev.off()

# ---------------------------------------------------------------------------
# 4. Heterogeneidade por bioma (H3)
# ---------------------------------------------------------------------------
m_am <- ddd(p[bioma == "Amazonia"])
m_ce <- ddd(p[bioma == "Cerrado"])
m_bio <- feols(as.formula(sprintf("y ~ ddd:i(bioma) | %s", fe)), data = p, cluster = vc)
tab4 <- etable(m_am, m_ce, m_bio, headers = c("Amazônia", "Cerrado", "Conjunto"))
print(tab4)
fwrite(as.data.table(tab4, keep.rownames = TRUE), "resultados/tabelas/tab4_biomas.csv")

# ---------------------------------------------------------------------------
# 5. Robustez
# ---------------------------------------------------------------------------
rob <- list()
rob[["Principal"]]            <- m_ddd
rob[["Risco contínuo (z)"]]   <- feols(as.formula(
  "y ~ mt:risco_z:pos | id + uf^bioma^ano + bioma^ano[risco_z]"), data = p, cluster = vc)
rob[["Corte no quartil"]]     <- ddd(p[, `:=`(alto_x = alto_q4, ddd_x = mt * alto_q4 * pos)],
                                     trat = "ddd_x", fe_ = "id + uf^bioma^ano + alto_x^bioma^ano")
rob[["Corte na mediana"]]     <- ddd(p[, `:=`(alto_x = alto_med, ddd_x = mt * alto_med * pos)],
                                     trat = "ddd_x", fe_ = "id + uf^bioma^ano + alto_x^bioma^ano")
rob[["Risco 2010-2014"]]      <- ddd(p[, `:=`(alto_x = alto_1014, ddd_x = mt * alto_1014 * pos)],
                                     trat = "ddd_x", fe_ = "id + uf^bioma^ano + alto_x^bioma^ano")
rob[["Até 2023 (sem fase 2)"]] <- ddd(p[ano <= 2023])
rob[["Com Tocantins"]]        <- ddd(p_all)
rob[["Sem controles < 100 km de MT"]] <- ddd(p[mt == 1 | dist_mt_km >= 100])
for (s in c("PA", "RO", "AM", "GO", "MS"))
  rob[[paste("Sem", s)]] <- ddd(p[uf != s])
rob[["Tendência linear MT × alto"]] <- ddd(p[, tend := mt * alto * (ano - 2017)], extra = "+ tend")
rob[["Placebo de data (2014; 2010-2017)"]] <- {
  q <- p[ano <= 2017][, ddd_x := mt * alto * (ano >= 2014)]
  ddd(q, trat = "ddd_x")
}

coef1 <- function(m) { ct <- coeftable(m)[1, ]; c(ct[1], ct[2], ct[4]) }
tab5 <- rbindlist(lapply(names(rob), function(n) {
  v <- coef1(rob[[n]])
  data.table(especificacao = n, beta = v[1], ep = v[2], p = v[3], n = nobs(rob[[n]]))
}))
print(tab5, digits = 3)
fwrite(tab5, "resultados/tabelas/tab5_robustez.csv")

# Vazamento como resultado: municípios de controle perto de MT (< 100 km),
# alto risco, depois de 2018, contra os demais controles
vz <- p[mt == 0][, `:=`(perto = as.integer(dist_mt_km < 100))]
vz[, ddd_x := perto * alto * pos]
m_vaz <- feols(y ~ ddd_x | id + uf^bioma^ano + alto^bioma^ano + perto^bioma^ano,
               data = vz, cluster = vc)
cat("\nVazamento (controles perto de MT):\n"); print(coeftable(m_vaz))
fwrite(data.table(beta = coef(m_vaz)[1], ep = se(m_vaz)[1], p = pvalue(m_vaz)[1],
                  unidades_perto = uniqueN(vz[perto == 1, id])),
       "resultados/tabelas/tab6_vazamento.csv")

# ---------------------------------------------------------------------------
# 6. Inferência com um único estado tratado
# ---------------------------------------------------------------------------
set.seed(2018)
b_mt <- coef(m_ddd)[["ddd"]]

# 6a. Permutação entre estados: cada estado faz o papel de "tratado"
perm_uf <- rbindlist(lapply(c("MT", "PA", "RO", "AM", "GO", "MS"), function(s) {
  q <- if (s == "MT") p else p[uf != "MT"]
  q <- copy(q)[, ddd_x := as.integer(uf == s) * alto * pos]
  data.table(uf = s, beta = coef(ddd(q, trat = "ddd_x"))[["ddd_x"]])
}))
p_perm_uf <- mean(abs(perm_uf$beta) >= abs(b_mt))
fwrite(perm_uf, "resultados/tabelas/tab7a_permutacao_estados.csv")

# 6b. Permutação entre regiões geográficas imediatas (RGI) dos estados de
#     controle: sorteia RGIs como "falso MT" até somar o mesmo nº de unidades
ctrl  <- p[mt == 0]
rgis  <- ctrl[, .(n = uniqueN(id)), by = cod_rgi]
n_alvo <- uniqueN(p[mt == 1, id])
B <- 500
perm_rgi <- numeric(B)
for (b in seq_len(B)) {
  ord <- rgis[sample(.N)]
  sel <- ord$cod_rgi[seq_len(which(cumsum(ord$n) >= n_alvo)[1])]
  q <- copy(ctrl)[, falso := as.integer(cod_rgi %in% sel)]
  q[, ddd_x := falso * alto * pos]
  perm_rgi[b] <- coef(feols(y ~ ddd_x | id + uf^bioma^ano + falso^bioma^ano +
                              alto^bioma^ano,
                            data = q))[["ddd_x"]]
}
p_perm_rgi <- mean(abs(perm_rgi) >= abs(b_mt))

# 6c. Intervalo à la Conley e Taber (2011): a distribuição de β̂ nos falsos
#     tratados (placebos RGI) aproxima o erro do único estado tratado.
ct_ic <- b_mt - quantile(perm_rgi, c(.975, .025))

inf <- data.table(
  metodo = c("Erro-padrão agrupado por município",
             "Permutação entre estados (6 posições)",
             sprintf("Permutação entre RGIs dos controles (%d sorteios)", B),
             "IC 95% à la Conley-Taber (placebos RGI)"),
  resultado = c(sprintf("EP = %.4f; p = %.3f; IC95 [%.4f; %.4f]", se(m_ddd)[1], pvalue(m_ddd)[1],
                        confint(m_ddd)[1, 1], confint(m_ddd)[1, 2]),
                sprintf("p = %.3f (MT em %d.º de 6 em |β|)", p_perm_uf,
                        rank(-abs(perm_uf$beta))[perm_uf$uf == "MT"]),
                sprintf("p = %.3f", p_perm_rgi),
                sprintf("[%.4f; %.4f]", ct_ic[1], ct_ic[2])))
print(inf)
fwrite(inf, "resultados/tabelas/tab7_inferencia.csv")
fwrite(data.table(beta_placebo = perm_rgi), "resultados/tabelas/tab7b_placebos_rgi.csv")

png("resultados/figuras/fig2_permutacao.png", width = 1800, height = 1000, res = 220)
par(mar = c(4, 4, 2.5, 1))
hist(perm_rgi, breaks = 40, col = "grey85", border = "white",
     xlim = range(c(perm_rgi, b_mt)), main = "Placebos: RGIs de controle como falso tratado",
     xlab = "β placebo (p.p. da área)", ylab = "Frequência", cex.main = 1)
abline(v = b_mt, col = "#b2182b", lwd = 2)
abline(v = perm_uf[uf != "MT", beta], col = "#2166ac", lty = 2)
legend("topleft", c("β MT", "β estados de controle"), col = c("#b2182b", "#2166ac"),
       lty = c(1, 2), lwd = c(2, 1), bty = "n", cex = .8)
dev.off()

# ---------------------------------------------------------------------------
# 7. HonestDiD (Rambachan e Roth, 2023) — se o pacote estiver instalado
# ---------------------------------------------------------------------------
if (requireNamespace("HonestDiD", quietly = TRUE)) {
  bh <- coef(es); Vh <- vcov(es)
  npre <- sum(grepl("ano::201[0-6]", names(bh))); npos <- length(bh) - npre
  l_vec <- rep(1 / npos, npos)                      # efeito médio 2018-2024
  orig  <- HonestDiD::constructOriginalCS(bh, Vh, npre, npos, l_vec = l_vec)
  rm_   <- HonestDiD::createSensitivityResults_relativeMagnitudes(
    bh, Vh, npre, npos, Mbarvec = c(0, .5, 1, 1.5, 2), l_vec = l_vec)
  hon <- rbind(data.table(Mbar = NA_real_, lb = as.numeric(orig$lb), ub = as.numeric(orig$ub), metodo = "Original"),
               data.table(Mbar = rm_$Mbar, lb = rm_$lb, ub = rm_$ub, metodo = "Magnitudes relativas"))
  print(hon)
  fwrite(hon, "resultados/tabelas/tab8_honestdid.csv")
}

# ---------------------------------------------------------------------------
# 8. Objetos para a conversão em CO2 (script 04)
# ---------------------------------------------------------------------------
saveRDS(list(m_ddd = m_ddd, es = es, es_bio = es_bio, m_am = m_am, m_ce = m_ce,
             m_vaz = m_vaz, media_pre = media_pre, inf = inf, perm_uf = perm_uf,
             p_perm_rgi = p_perm_rgi, ct_ic = ct_ic, ddd_mao = ddd_mao),
        "resultados/modelos.rds")
cat("\nMédia pré-programa (MT, alto risco):", round(media_pre, 4), "% da área/ano\n")
