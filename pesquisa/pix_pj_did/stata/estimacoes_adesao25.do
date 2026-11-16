/*==============================================================================
  Efeito causal da chegada do Pix PJ sobre a inclusão digital-financeira
  dos pequenos negócios — DiD com tratamento escalonado (Stata)

  Tratamento : G_adesao25 = 1º mês em que >= 25% dos estabelecimentos ativos
               do município recebem Pix (coorte em AAAAMM; G_adesao25_t no
               índice de período 1..72, jan/2019 = 1).
  Amostra    : 40 municípios de MT, MS e GO com 50 a 600 mil hab. (2019).
  Painel     : município x mês, jan/2019 a dez/2024.

  Seções
    0. Configuração e instalação dos pacotes
    1. Dados e descrição das coortes
    2. TWFE de referência (eq. 1)                       -> reghdfe
    3. Decomposição de Goodman-Bacon (2021)             -> bacondecomp
    4. Callaway e Sant'Anna (2021), estimador principal -> csdid
    5. Sun e Abraham (2021)                             -> eventstudyinteract
    6. Borusyak, Jaravel e Spiess (2024)                -> did_imputation
    7. Sensibilidade: Rambachan e Roth (2023)           -> honestdid
    8. Placebo temporal (adoção fictícia 6 meses antes)
    9. Heterogeneidade por UF e por porte

  Como usar: ajuste o caminho em "global RAIZ" e rode o arquivo inteiro.
  Resultados: pasta stata/resultados (log, tabelas .csv e gráficos .png).
==============================================================================*/

version 16
clear all
set more off
set seed 20240901

* >>> AJUSTE AQUI: pasta pix_pj_did do repositório no seu computador <<<
global RAIZ "C:/Users/SEU_USUARIO/econometrics/pesquisa/pix_pj_did"

global DADOS "$RAIZ/dados"
global RES   "$RAIZ/stata/resultados"
capture mkdir "$RAIZ/stata"
capture mkdir "$RES"
capture log close
log using "$RES/estimacoes_adesao25.log", replace text

*------------------------------------------------------------------------------
* 0. Pacotes (rode uma vez; depois pode comentar)
*------------------------------------------------------------------------------
foreach p in ftools reghdfe drdid csdid avar eventstudyinteract ///
             did_imputation bacondecomp coefplot estout {
    capture which `p'
    if _rc ssc install `p', replace
}
capture reghdfe, compile
capture which honestdid
if _rc {
    net install honestdid, from("https://raw.githubusercontent.com/mcaceresb/stata-honestdid/main") replace
    honestdid _plugin_check
}

*------------------------------------------------------------------------------
* 1. Dados
*------------------------------------------------------------------------------
import delimited "$DADOS/painel_pix_pj_mensal_amostra40.csv", ///
    clear encoding(utf8) case(preserve)

* variável de coorte no formato do csdid: 0 = nunca tratado
rename G_adesao25_t g
xtset id periodo
encode uf, gen(uf_n)

* Resultados (versões asinh para variáveis com assimetria; ver seção 3.6 vi)
*   y1 = transações Pix PJ por empresa ativa  (CNPJ: até set/2024 = período 69)
*   y2 = aberturas de MEI                      (CNPJ: até set/2024)
*   y3 = IHH do crédito bancário               (ESTBAN: até dez/2024)
*   y5 = crédito bancário per capita           (ESTBAN: até dez/2024)
gen y1 = asinh_y1_pix_pj_por_empresa
gen y2 = asinh_y2_aberturas_mei
gen y3 = y3_ihh_credito
gen y5 = asinh_y5_credito_pc
label var y1 "asinh(Pix PJ por empresa)"
label var y2 "asinh(aberturas de MEI)"
label var y3 "IHH do crédito"
label var y5 "asinh(crédito per capita)"

* último período disponível de cada resultado (painel balanceado)
local tmax_y1 69
local tmax_y2 69
local tmax_y3 72
local tmax_y5 72
global Y "y1 y2 y3 y5"

* covariáveis pré-tratamento (fixas no tempo). 'campus' = 1 em todos os 40
* municípios (sem variação) e por isso fica de fora.
global X "ln_pop_2019 idhm_2010 ln_pib_pc_2019 pct_simples_2019"

* Descrição das coortes
preserve
    bysort id: keep if _n == 1
    tab G_adesao25
    tab G_adesao25 uf
    count if g == 0
    display as text "Municípios nunca tratados (até o fim do painel): " r(N)
restore
* Como todos os 40 municípios acabam tratados, o grupo de controle é o dos
* "ainda não tratados" (opção notyet do csdid), como na seção 3.6 (iii).

* tempo relativo à adoção (para os estudos de evento)
gen rel = periodo - g if g > 0

*------------------------------------------------------------------------------
* 2. TWFE de referência (eq. 1) — apenas para comparação
*------------------------------------------------------------------------------
eststo clear
foreach y of global Y {
    eststo twfe_`y': reghdfe `y' D_adesao25 if periodo <= `tmax_`y'', ///
        absorb(id periodo) vce(cluster id)
}
esttab twfe_* using "$RES/tab_twfe.csv", replace se star(* 0.10 ** 0.05 *** 0.01) ///
    keep(D_adesao25) mtitles($Y) title("TWFE: efeito de D_adesao25")
esttab twfe_*, se star(* 0.10 ** 0.05 *** 0.01) keep(D_adesao25) mtitles($Y)

*------------------------------------------------------------------------------
* 3. Decomposição de Goodman-Bacon (2021)
*------------------------------------------------------------------------------
foreach y of global Y {
    preserve
        keep if periodo <= `tmax_`y''
        display as result _n "===== Bacon: `y' ====="
        capture noisily bacondecomp `y' D_adesao25, ddetail
        if !_rc graph export "$RES/bacon_`y'.png", replace width(1600)
    restore
}

*------------------------------------------------------------------------------
* 4. Callaway e Sant'Anna (2021) — estimador principal
*    Controle: ainda não tratados. Bootstrap multiplicador (wild), cluster id.
*    'long2' usa diferenças longas também no pré-período (necessário para o
*    HonestDiD e para leitura padrão do estudo de evento).
*------------------------------------------------------------------------------
tempname R
matrix `R' = J(4, 6, .)
matrix colnames `R' = ATT_simples ep_simples ATT_pre ep_pre ATT_pos ep_pos
matrix rownames `R' = $Y
local i = 0
foreach y of global Y {
    local ++i
    display as result _n "===== Callaway-Sant'Anna (sem covariáveis): `y' ====="
    csdid `y' if periodo <= `tmax_`y'', ivar(id) time(periodo) gvar(g) ///
        notyet long2 wboot rseed(20240901)
    estimates store cs_`y'

    * (iii) efeito agregado
    estat simple
    matrix `R'[`i', 1] = el(r(b), 1, 1)
    matrix `R'[`i', 2] = sqrt(el(r(V), 1, 1))

    * (ii) efeito por coorte  e  efeito por mês-calendário
    estat group
    estat calendar

    * (i) efeito dinâmico (event study), 12 meses antes a 24 depois
    estat event, window(-12 24) estore(ev_`y')
    matrix `R'[`i', 3] = el(r(b), 1, 1)        // Pre_avg
    matrix `R'[`i', 4] = sqrt(el(r(V), 1, 1))
    matrix `R'[`i', 5] = el(r(b), 1, 2)        // Post_avg
    matrix `R'[`i', 6] = sqrt(el(r(V), 2, 2))
    csdid_plot, title("CS: `: var label `y''") ///
        xtitle("Meses em relação à adesão") ytitle("ATT")
    graph export "$RES/cs_evento_`y'.png", replace width(1600)

    * teste conjunto de tendências paralelas no pré-tratamento
    estat pretrend
}
matrix list `R', format(%9.4f)
putexcel set "$RES/tab_cs_agregados.xlsx", replace
putexcel A1 = matrix(`R'), names nformat("0.0000")

* Versão com covariáveis (duplamente robusta, eq. 3 com IPW).
* Atenção: há coortes com 1 município; o escore de propensão pode não
* convergir nelas. Por isso usamos 'capture' e, se falhar, a regressão de
* resultado (method(reg)).
foreach y of global Y {
    display as result _n "===== Callaway-Sant'Anna com covariáveis (DR): `y' ====="
    capture noisily csdid `y' $X if periodo <= `tmax_`y'', ivar(id) ///
        time(periodo) gvar(g) notyet method(dripw) wboot rseed(20240901)
    if _rc {
        display as error "dripw falhou; usando method(reg)"
        capture noisily csdid `y' $X if periodo <= `tmax_`y'', ivar(id) ///
            time(periodo) gvar(g) notyet method(reg) wboot rseed(20240901)
    }
    if !_rc {
        estat simple
        estat event, window(-12 24)
    }
}

*------------------------------------------------------------------------------
* 5. Sun e Abraham (2021) — eq. 4
*    Coorte de controle = a última a ser tratada; usa só os meses anteriores
*    à adoção dessa coorte. Referência k = -1. Extremos agrupados (bins).
*------------------------------------------------------------------------------
quietly summarize g if g > 0
local glast = r(max)
gen ultima = (g == `glast')

local leads ""
local lags ""
forvalues k = 12(-1)2 {
    gen F`k' = (rel == -`k') & !ultima
    local leads "`leads' F`k'"
}
replace F12 = (rel <= -12) & !ultima       // agrupa k <= -12
forvalues k = 0/24 {
    gen L`k' = (rel == `k') & !ultima
    local lags "`lags' L`k'"
}
replace L24 = (rel >= 24 & rel < .) & !ultima   // agrupa k >= 24

foreach y of global Y {
    display as result _n "===== Sun-Abraham: `y' ====="
    capture noisily eventstudyinteract `y' `leads' `lags' ///
        if periodo < `glast' & periodo <= `tmax_`y'', ///
        cohort(g) control_cohort(ultima) absorb(id periodo) vce(cluster id)
    if !_rc {
        matrix b = e(b_iw)
        matrix V = e(V_iw)
        ereturn post b V
        estimates store sa_`y'
        coefplot sa_`y', vertical yline(0) xlabel(, angle(90) labsize(vsmall)) ///
            title("Sun-Abraham: `: var label `y''")
        graph export "$RES/sa_evento_`y'.png", replace width(1600)
    }
}

*------------------------------------------------------------------------------
* 6. Borusyak, Jaravel e Spiess (2024) — imputação
*------------------------------------------------------------------------------
gen g_bjs = g if g > 0      // o did_imputation usa missing para nunca tratados
foreach y of global Y {
    display as result _n "===== BJS (imputação): `y' ====="
    capture noisily did_imputation `y' id periodo g_bjs if periodo <= `tmax_`y'', ///
        allhorizons pretrends(12) autosample minn(0)
    if !_rc estimates store bjs_ev_`y'
    capture noisily did_imputation `y' id periodo g_bjs if periodo <= `tmax_`y'', ///
        autosample                      // efeito médio agregado
    if !_rc estimates store bjs_`y'
}

*------------------------------------------------------------------------------
* 7. Rambachan e Roth (2023) — HonestDiD sobre o estudo de evento do CS
*    Janela -12..12: em e(b), posições 1-2 = Pre_avg e Post_avg,
*    3-13 = Tm12..Tm2 (Tm1 é a referência no long2), 14-26 = Tp0..Tp12.
*    Relative magnitudes: quanto a violação pós pode ser M vezes a maior
*    violação observada no pré-período.
*------------------------------------------------------------------------------
foreach y of global Y {
    display as result _n "===== HonestDiD (CS): `y' ====="
    quietly csdid `y' if periodo <= `tmax_`y'', ivar(id) time(periodo) ///
        gvar(g) notyet long2
    quietly estat event, window(-12 12) estore(hd_`y')
    estimates restore hd_`y'
    capture noisily honestdid, pre(3/13) post(14/26) mvec(0.5(0.5)2) ///
        coefplot xtitle("M") ytitle("IC robusto (95%)")
    if !_rc graph export "$RES/honestdid_`y'.png", replace width(1600)
}

*------------------------------------------------------------------------------
* 8. Placebo temporal: adoção fictícia 6 meses antes da real, usando apenas
*    os meses anteriores à adoção verdadeira (espera-se ATT = 0).
*------------------------------------------------------------------------------
gen g_placebo = cond(g > 6, g - 6, 0)
foreach y of global Y {
    display as result _n "===== Placebo (-6 meses): `y' ====="
    preserve
        keep if periodo < g & periodo <= `tmax_`y''
        capture noisily csdid `y', ivar(id) time(periodo) gvar(g_placebo) ///
            notyet wboot rseed(20240901)
        if !_rc estat simple
    restore
}

*------------------------------------------------------------------------------
* 9. Heterogeneidade (seção 3.6 vii) — atenção: poucos municípios por grupo
*------------------------------------------------------------------------------
* por porte: população 2019 abaixo/acima da mediana da amostra
preserve
    bysort id: keep if _n == 1
    quietly summarize pop_2019, detail
    local med = r(p50)
restore
gen h_pequeno = pop_2019 <  `med'
gen h_grande  = pop_2019 >= `med'
gen h_GO      = uf == "GO"
gen h_MTMS    = inlist(uf, "MT", "MS")

foreach y of global Y {
    foreach grupo in h_pequeno h_grande h_GO h_MTMS {
        display as result _n "===== Heterogeneidade `y' | `grupo' ====="
        capture noisily csdid `y' if periodo <= `tmax_`y'' & `grupo' == 1, ///
            ivar(id) time(periodo) gvar(g) notyet wboot rseed(20240901)
        if !_rc estat simple
    }
}
* MT (10) e MS (7) têm poucos municípios para estimar em separado; por isso
* aparecem juntos. Para H4 (IDF-MT inicial), junte o índice e repita o bloco
* acima com o grupo "idf_2019 < mediana".

log close
display as result "Fim. Resultados em $RES"
