# =============================================================================
# REM MT e desmatamento — triplas diferenças (DDD)
# 01_download.R — baixa os dados públicos usados no projeto
#
# Execute a partir da pasta rem_mt/:   Rscript R/01_download.R
# Os arquivos vão para dados_brutos/ (não precisam ser baixados de novo).
# =============================================================================

dir.create("dados_brutos", showWarnings = FALSE)
options(timeout = 600)

baixa <- function(url, destino) {
  if (file.exists(destino)) return(invisible(destino))
  message("Baixando ", basename(destino))
  download.file(url, destino, mode = "wb", quiet = TRUE)
}

# 1. PRODES/INPE por município (painel do TerraBrasilis) -----------------------
#    data_*      = área desmatada (km²) por período PRODES (ago/t-1 a jul/t)
#    loinames_*  = dicionário gid -> município (com código IBGE)
api <- "https://terrabrasilis.dpi.inpe.br/app/prodes/dashboard/deforestation/files/"
for (b in c("amazon", "cerrado", "legal_amazon")) {
  baixa(paste0(api, "data/prodes_", b, ".json"),
        paste0("dados_brutos/data_prodes_", b, ".json"))
  baixa(paste0(api, "config/loinames/prodes_", b, ".json"),
        paste0("dados_brutos/config_loinames_prodes_", b, ".json"))
}

# 2. IBGE — área territorial dos municípios (2022) -----------------------------
baixa(paste0("https://geoftp.ibge.gov.br/organizacao_do_territorio/",
             "estrutura_territorial/areas_territoriais/2022/",
             "AR_BR_RG_UF_RGINT_MES_MIC_MUN_2022.xls"),
      "dados_brutos/AR_BR_RG_UF_RGINT_MES_MIC_MUN_2022.xls")

# 3. IBGE/SIDRA — rebanho bovino (PPM, tab. 3939) e área plantada de soja
#    (PAM, tab. 1612), por município, 2010-2024
ufs <- c(MT = 51, PA = 15, RO = 11, AM = 13, GO = 52, MS = 50, TO = 17)
for (uf in ufs) {
  baixa(sprintf(paste0("https://apisidra.ibge.gov.br/values/t/3939/n6/in%%20n3%%20%d/",
                       "v/105/p/2010-2024/c79/2670?formato=json"), uf),
        sprintf("dados_brutos/sidra_bov_%d.json", uf))
  baixa(sprintf(paste0("https://apisidra.ibge.gov.br/values/t/1612/n6/in%%20n3%%20%d/",
                       "v/109/p/2010-2024/c81/2713?formato=json"), uf),
        sprintf("dados_brutos/sidra_soja_%d.json", uf))
}

# 4. IBGE — localidades 2022 (coordenadas das sedes e das localidades de MT)
#    Usadas para (a) a distância até MT (teste de vazamento) e
#    (b) as regiões geográficas imediatas (RGI) na inferência por permutação.
if (!file.exists("dados_brutos/sedes_municipais_2022.csv")) {
  zipf <- file.path(tempdir(), "loc.zip")
  download.file(paste0("https://geoftp.ibge.gov.br/organizacao_do_territorio/",
                       "estrutura_territorial/localidades/Localidades_do_Brasil/",
                       "2022/Localidades_Brasil_shp.zip"), zipf, mode = "wb")
  unzip(zipf, exdir = file.path(tempdir(), "loc"))
  loc <- foreign::read.dbf(file.path(tempdir(), "loc", "BR_localidades_2022.dbf"),
                           as.is = TRUE)
  sedes <- subset(loc, SCT_LOCALI == "Sede Municipal",
                  c(CD_MUN, NM_MUN, SIGLA_UF, CD_RGI, LAT_LOCALI, LONG_LOCAL))
  names(sedes) <- c("cod_ibge", "municipio", "uf", "cod_rgi", "lat", "lon")
  write.csv(sedes, "dados_brutos/sedes_municipais_2022.csv", row.names = FALSE)
  mt <- subset(loc, SIGLA_UF == "MT", c(CD_MUN, LAT_LOCALI, LONG_LOCAL))
  names(mt) <- c("cod_ibge", "lat", "lon")
  write.csv(mt, "dados_brutos/localidades_MT_2022.csv", row.names = FALSE)
}

message("Download concluído.")
