# Conteúdo 8 — Controle sintético (Estatística e Econometria, PROFINIT)
# Execute a partir desta pasta (codigo/).

library(tidysynth)   # install.packages("tidysynth")
library(dplyr)
df <- read.csv("../dados/painel_sintetico.csv")

sc <- df |>
  synthetic_control(outcome = y, unit = unidade, time = ano,
                    i_unit = "Tratado", i_time = 2012,
                    generate_placebos = TRUE) |>
  generate_predictor(time_window = 2000:2005, y_00_05 = mean(y)) |>
  generate_predictor(time_window = 2006:2011, y_06_11 = mean(y)) |>
  generate_predictor(time_window = 2011, y_2011 = y) |>
  generate_weights(optimization_window = 2000:2011) |>
  generate_control()

sc |> plot_trends()          # tratado x sintético
sc |> plot_differences()     # trajetória do efeito
sc |> plot_weights()
sc |> plot_placebos()        # placebos no espaço
sc |> grab_significance()    # razão RMSPE e p-valor de permutação
