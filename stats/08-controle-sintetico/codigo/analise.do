* Conteúdo 8 — Controle sintético (Estatística e Econometria, PROFINIT)
* Execute a partir desta pasta (codigo/).

* ssc install synth ; ssc install synth_runner
import delimited "../dados/painel_sintetico.csv", clear
encode unidade, generate(id)          // "Tratado" recebe id = 16 (ordem alfabética)
tsset id ano

* Preditores: o resultado em cada ano pré-tratamento
local preds
forvalues a = 2000/2011 {
    local preds `preds' y(`a')
}
synth y `preds', trunit(16) trperiod(2012) fig
matrix list e(W_weights)

* Placebos no espaço, p-valores e gráficos
synth_runner y `preds', trunit(16) trperiod(2012) gen_vars
effect_graphs
pval_graphs
