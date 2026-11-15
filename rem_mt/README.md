# REM MT e desmatamento — triplas diferenças (DDD)

Código e dados do projeto *Efeito do Programa REM MT sobre o desmatamento: uma
abordagem de triplas diferenças*. Tudo usa dados públicos e roda em R.

## Como rodar

A partir desta pasta (`rem_mt/`):

```bash
Rscript R/01_download.R            # baixa PRODES (INPE), IBGE e SIDRA para dados_brutos/
Rscript R/02_painel.R              # monta dados/painel_rem_mt.csv
Rscript R/03_estimacao.R           # DDD, estudo de eventos, biomas, robustez, inferência
Rscript R/04_co2_adicionalidade.R  # área e tCO2e evitadas, linha de base histórica
python3 R/05_relatorio.py          # gera resultados/Resultados_DDD_REM_MT.docx
```

Pacotes R: `data.table`, `jsonlite`, `readxl`, `fixest`, `HonestDiD` (opcional).
O relatório usa Python com `python-docx`.

## Estrutura

| Pasta/arquivo | Conteúdo |
|---|---|
| `dados_brutos/` | arquivos originais (PRODES JSON do TerraBrasilis, áreas IBGE 2022, SIDRA, sedes municipais) |
| `dados/painel_rem_mt.csv` | painel município × bioma × ano (2010–2024) |
| `resultados/tabelas/` | todas as tabelas em CSV (`tab1` … `tab10`) |
| `resultados/figuras/` | estudo de eventos, permutação, linha de base de MT |
| `resultados/Resultados_DDD_REM_MT.docx` | relatório de resultados |

## Dicionário do painel

| Variável | Descrição |
|---|---|
| `id` | município × bioma (unidade do painel) |
| `cod_ibge`, `municipio`, `uf`, `bioma` | identificação |
| `ano` | ano PRODES (ago/t-1 a jul/t) |
| `km2` | desmatamento PRODES no ano (km²) |
| `y` | desmatamento em % da área municipal (resultado principal) |
| `asinh_km2` | asinh(km²) (resultado alternativo) |
| `risco` | desmatamento médio anual 2012–2016, % da área |
| `alto` | 1 = tercil superior de `risco` dentro do estado × bioma |
| `alto_q4`, `alto_med`, `alto_1014`, `risco_z` | definições alternativas de risco |
| `mt`, `pos`, `ddd` | MT; ano ≥ 2018; MT × alto × pós |
| `bov_ini`, `soja_ini` | bois/km² e % da área com soja, média 2010–2012 |
| `dist_mt_km` | distância da sede até a localidade de MT mais próxima |
| `cod_rgi` | região geográfica imediata (IBGE), usada na permutação |

## Diferenças em relação ao projeto escrito

1. **Denominador da taxa**: área municipal (IBGE 2022), não a floresta
   remanescente de 2008, que exige processar os mapas do PRODES em SIG.
2. **Cerrado**: o PRODES Cerrado é bienal até 2012; o painel do Cerrado é
   anual de 2013 a 2024 (5 anos antes do programa, não 8).
3. **Covariáveis**: no lugar de preços CEPEA × estrutura inicial, usa-se
   estrutura inicial (bois/km², % soja) × dummies de ano, que absorve qualquer
   choque nacional de preços.
4. **Não estimados nesta versão** (dependem de dados por LAI ou não abertos
   por município): canal da fiscalização (autuações SEMA-MT/IBAMA), dose
   (investimentos do REM), MapBiomas como medida alternativa, precipitação.
5. **Fatores de emissão** são provisórios (Amazônia 550 e Cerrado 200
   tCO2e/ha) e devem ser trocados pelos do FREL/Inventário Nacional.
