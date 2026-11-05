* Conteúdo 3 — Estudo de caso: o reel da Selic e do déficit (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/.

import excel "../../dados_caso/correlacao_causalidade_sintetica.xlsx", sheet("Fiscal_Selic") firstrow clear
correlate superavit_primario selic
bysort regime: correlate superavit_primario selic        // Simpson
pcorr selic superavit_primario inflacao                  // correlação parcial (controla a inflação)

import excel "../../dados_caso/correlacao_causalidade_sintetica.xlsx", sheet("Sorvete_Afogamento") firstrow clear
pcorr afogamentos sorvetes_vendidos temperatura_c         // correlação parcial

* Tarefa: ssc install sgsbcb (ou importe os CSVs baixados do SGS/BCB)
