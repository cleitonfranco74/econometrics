* Estudos de caso — 04-regressao-multipla (Estatística e Econometria, PROFINIT)
* Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

* 8.1 wage1
use "../../dados_caso/wage1.dta", clear
regress LWAGE EDUC EXPER TENURE
lincom EXPER + TENURE                        // efeito de +1 ano na mesma empresa
regress LWAGE EDUC c.EXPER##c.EXPER c.TENURE##c.TENURE FEMALE MARRIED NONWHITE, robust

* 8.2 PNAD
use "../../dados_caso/pnad_2009_2011_internet_renda.dta", clear
keep if Renda > 0
generate logrenda = ln(Renda)
regress logrenda internet lereescrever anosestudo horas_trabalhadas genero idade raça estcivil, robust
regress logrenda internet lereescrever anosestudo i.horas_trabalhadas genero c.idade##c.idade ///
    i.raça i.estcivil i.uf i.ano, robust

* 8.4 SAMU
use "../../dados_caso/samu_mt_2000_2020.dta", clear
generate logmortes = ln(mortes_transito + 1)
generate lpop = ln(pop)
regress logmortes samu, vce(cluster cod_mun)
regress logmortes samu equipamentos ortopedista tx_analfa, vce(cluster cod_mun)
regress logmortes samu equipamentos ortopedista tx_analfa lpop, vce(cluster cod_mun)

* 8.5 Empresas (exemplo: Amazon)
import excel "../../dados_caso/estudos_caso_regressao_multipla.xlsx", sheet("Amazon") firstrow clear
describe
regress ReceitadeVendasOnlinebiUSD InvestimentoemLogísticabiUSD-AvaliaçãoMédiadoCliente15
estat vif
