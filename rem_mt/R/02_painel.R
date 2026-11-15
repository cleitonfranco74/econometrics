# =============================================================================
# 02_painel.R — monta o painel município × bioma × ano
#
# Unidade de análise: a porção de cada município em um bioma (Amazônia ou
# Cerrado), como o PRODES mede o desmatamento. Municípios de MT que estão nos
# dois biomas aparecem duas vezes (uma por bioma) e são agrupados pelo código
# IBGE na hora de calcular os erros-padrão.
#
# Saída: dados/painel_rem_mt.csv
# =============================================================================

suppressPackageStartupMessages({
  library(data.table); library(jsonlite); library(readxl)
})

# ---------------------------------------------------------------------------
# 1. PRODES: lê o JSON do TerraBrasilis e devolve município × período
# ---------------------------------------------------------------------------
le_prodes <- function(bioma) {
  cfg <- fromJSON(sprintf("dados_brutos/config_loinames_prodes_%s.json", bioma),
                  simplifyVector = FALSE)
  mun <- Filter(function(l) l$name == "mun", cfg$lois)[[1]]$loinames
  dic <- rbindlist(lapply(mun, function(x)
    data.table(gid = x$gid, nome = x$loiname, cod_ibge = x$codibge)))

  dat <- fromJSON(sprintf("dados_brutos/data_prodes_%s.json", bioma),
                  simplifyVector = FALSE)
  obs <- rbindlist(lapply(dat$periods, function(p) {
    f <- Filter(function(z) z$loi == 2, p$features)        # loi 2 = município
    if (!length(f)) return(NULL)
    data.table(gid    = vapply(f, function(z) z$loiname, numeric(1)),
               ano_ini = p$startDate$year,
               ano    = p$endDate$year,
               km2    = vapply(f, function(z) sum(vapply(z$areas, function(a) a$area,
                                                         numeric(1))), numeric(1)))
  }))
  # O JSON só traz municípios com desmatamento > 0: completa os zeros
  periodos <- unique(obs[, .(ano_ini, ano)])
  grade <- CJ(gid = dic$gid, ano = periodos$ano)[periodos, on = "ano"]
  out <- obs[grade, on = c("gid", "ano", "ano_ini")]
  out[is.na(km2), km2 := 0]
  out <- dic[out, on = "gid"]
  out[, bioma := fifelse(bioma == "amazon", "Amazonia", "Cerrado")]
  out[]
}

prodes <- rbind(le_prodes("amazon"), le_prodes("cerrado"))
prodes[, uf_nome := sub(".*_", "", nome)]

# Período PRODES: o "ano t" vai de 1º/ago de t-1 a 31/jul de t.
# Amazônia: anual desde 2008. Cerrado: bienal até 2012, anual desde 2013.
prodes[, anual := (ano - ano_ini) == 1]

# ---------------------------------------------------------------------------
# 2. Área municipal (IBGE 2022) e sedes (coordenadas, região imediata)
# ---------------------------------------------------------------------------
area <- as.data.table(read_excel("dados_brutos/AR_BR_RG_UF_RGINT_MES_MIC_MUN_2022.xls",
                                 sheet = "AR_BR_MUN_2022"))
area <- area[!is.na(CD_MUN), .(cod_ibge = as.integer(CD_MUN), uf = NM_UF_SIGLA,
                               area_km2 = as.numeric(AR_MUN_2022))]
sedes <- fread("dados_brutos/sedes_municipais_2022.csv")[, .(cod_ibge, municipio, cod_rgi, lat, lon)]

prodes <- area[prodes, on = "cod_ibge"]
prodes <- sedes[prodes, on = "cod_ibge"]

# ---------------------------------------------------------------------------
# 3. Risco de desmatamento antes do programa (medido longe da seleção de MT)
#    Risco = desmatamento médio anual 2012-2016 / área do município (% a.a.)
#    No Cerrado, o período PRODES "2012" é bienal (ago/2010-jul/2012):
#    entra dividido por 2 como aproximação do ano 2012.
#    Versão alternativa (robustez): janela 2010-2014.
# ---------------------------------------------------------------------------
risco <- prodes[, {
  a <- function(y) { v <- km2[ano == y]; if (!length(v)) NA_real_ else v }
  am <- bioma[1] == "Amazonia"
  r1216 <- if (am) mean(sapply(2012:2016, a)) else
    (a(2012) / 2 + sum(sapply(2013:2016, a))) / 5
  # 2010-2014: Amazônia anual; Cerrado = (2012 bienal + 2013 + 2014) / 4 anos
  r1014 <- if (am) mean(sapply(2010:2014, a)) else (a(2012) + a(2013) + a(2014)) / 4
  .(risco = 100 * r1216 / area_km2[1], risco_1014 = 100 * r1014 / area_km2[1])
}, by = .(cod_ibge, bioma)]

# ---------------------------------------------------------------------------
# 4. Amostra principal
#    Amazônia: MT (tratado), PA, RO, AM (controles)
#    Cerrado:  MT (tratado), GO, MS (controles)
#    Tocantins (ambos os biomas) fica fora do principal; entra na robustez.
#    Acre fica fora (REM Acre sobreposto). Pantanal não é medido pelo PRODES
#    Amazônia/Cerrado, portanto já fica de fora.
# ---------------------------------------------------------------------------
painel <- prodes[anual == TRUE & ano %between% c(2010, 2024)]
painel <- risco[painel, on = c("cod_ibge", "bioma")]
painel <- painel[(bioma == "Amazonia" & uf %in% c("MT", "PA", "RO", "AM", "TO")) |
                 (bioma == "Cerrado"  & uf %in% c("MT", "GO", "MS", "TO"))]

# Faixas de risco DENTRO de cada estado × bioma (tercil, quartil, mediana)
painel[, `:=`(
  alto      = as.integer(risco >= quantile(risco, 2/3, na.rm = TRUE)),
  alto_q4   = as.integer(risco >= quantile(risco, 3/4, na.rm = TRUE)),
  alto_med  = as.integer(risco >= quantile(risco, 1/2, na.rm = TRUE)),
  alto_1014 = as.integer(risco_1014 >= quantile(risco_1014, 2/3, na.rm = TRUE)),
  risco_z   = (risco - mean(risco, na.rm = TRUE)) / sd(risco, na.rm = TRUE)
), by = .(uf, bioma)]
# (os quantis são calculados uma vez por unidade: cada unidade tem o mesmo
#  valor de risco em todos os anos, e o painel anual é balanceado por bioma)

# ---------------------------------------------------------------------------
# 5. Covariáveis: estrutura produtiva inicial (2010-2012)
#    bov_ini  = cabeças de gado por km² ; soja_ini = % da área com soja
#    No modelo entram interagidas com dummies de ano: absorvem qualquer choque
#    nacional de preços (boi, soja) que atinja mais os municípios pecuários ou
#    sojicultores — versão flexível de "preço × participação inicial".
# ---------------------------------------------------------------------------
le_sidra <- function(arq) {
  x <- fromJSON(arq)[-1, ]
  data.table(cod_ibge = as.integer(x$D1C), ano = as.integer(x$D3C),
             valor = suppressWarnings(as.numeric(x$V)))
}
bov  <- rbindlist(lapply(Sys.glob("dados_brutos/sidra_bov_*.json"),  le_sidra))
soja <- rbindlist(lapply(Sys.glob("dados_brutos/sidra_soja_*.json"), le_sidra))
ini <- merge(bov[ano %in% 2010:2012, .(bov = mean(valor, na.rm = TRUE)), by = cod_ibge],
             soja[ano %in% 2010:2012, .(soja = mean(fcoalesce(valor, 0))), by = cod_ibge],
             by = "cod_ibge", all = TRUE)
painel <- ini[painel, on = "cod_ibge"]
painel[, `:=`(bov_ini  = fcoalesce(bov, 0) / area_km2,
              soja_ini = 100 * fcoalesce(soja, 0) / (area_km2 * 100))]
painel[, c("bov", "soja") := NULL]

# ---------------------------------------------------------------------------
# 6. Distância até MT (vazamento): menor distância entre a sede do município
#    e qualquer localidade de MT (cidades, vilas, povoados — IBGE 2022).
#    Aproximação da distância até a divisa estadual.
# ---------------------------------------------------------------------------
loc_mt <- fread("dados_brutos/localidades_MT_2022.csv")
hav <- function(lat1, lon1, lat2, lon2) {
  r <- pi / 180
  a <- sin((lat2 - lat1) * r / 2)^2 +
       cos(lat1 * r) * cos(lat2 * r) * sin((lon2 - lon1) * r / 2)^2
  2 * 6371 * asin(sqrt(a))
}
cods <- unique(painel[uf != "MT", .(cod_ibge, lat, lon)])
cods[, dist_mt_km := mapply(function(a, b) min(hav(a, b, loc_mt$lat, loc_mt$lon)), lat, lon)]
painel <- cods[, .(cod_ibge, dist_mt_km)][painel, on = "cod_ibge"]
painel[uf == "MT", dist_mt_km := 0]

# ---------------------------------------------------------------------------
# 7. Variáveis do modelo
# ---------------------------------------------------------------------------
painel[, `:=`(
  id        = paste(cod_ibge, bioma, sep = "_"),
  mt        = as.integer(uf == "MT"),
  pos       = as.integer(ano >= 2018),
  y         = 100 * km2 / area_km2,          # desmatamento anual, % da área
  asinh_km2 = asinh(km2)
)]
painel[, ddd := mt * alto * pos]

setcolorder(painel, c("id", "cod_ibge", "municipio", "uf", "bioma", "ano",
                      "km2", "area_km2", "y", "asinh_km2", "risco", "alto",
                      "mt", "pos", "ddd"))
setorder(painel, uf, bioma, cod_ibge, ano)
painel[, c("gid", "nome", "uf_nome", "anual", "ano_ini") := NULL]

dir.create("dados", showWarnings = FALSE)
fwrite(painel, "dados/painel_rem_mt.csv")

# Resumo
cat("Painel salvo em dados/painel_rem_mt.csv\n")
print(painel[uf != "TO", .(unidades = uniqueN(id), alto_risco = uniqueN(id[alto == 1]),
                           anos = paste(range(ano), collapse = "-")), by = .(bioma, uf)])
