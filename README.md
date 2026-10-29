# Econometrics

Materiais didáticos de Estatística e Econometria (Mestrado PROFINIT).

Comece pelo índice: [`stats/index.html`](stats/index.html).

## Conteúdos (`stats/`)

| Conteúdo | Tema | Página |
|---|---|---|
| 2 | Medidas descritivas | [`02-medidas-descritivas`](stats/02-medidas-descritivas/index.html) |
| 3 | Correlação, causalidade e regressão linear simples | [`03-correlacao-causalidade-regressao`](stats/03-correlacao-causalidade-regressao/index.html) |
| 4 | Regressão linear múltipla | [`04-regressao-multipla`](stats/04-regressao-multipla/index.html) |
| 5 | Dados em painel | [`05-dados-em-painel`](stats/05-dados-em-painel/index.html) |
| 6 | Diferenças em diferenças | [`06-diferencas-em-diferencas`](stats/06-diferencas-em-diferencas/index.html) |
| 7 | Regressão descontínua | [`07-regressao-descontinua`](stats/07-regressao-descontinua/index.html) |
| 8 | Controle sintético | [`08-controle-sintetico`](stats/08-controle-sintetico/index.html) |

Cada conteúdo é uma página HTML que abre direto no navegador, com teoria e
fórmulas, exemplo aplicado, código em Python, R e Stata, simulador interativo
e exercícios com gabarito. Os dados ficam em `dados/` e os scripts em `codigo/`
de cada conteúdo (execute-os de dentro da pasta `codigo/`). Estilos e funções
comuns estão em `stats/assets/`.

### Dados

Os exemplos dos Conteúdos 3 a 8 usam dados **simulados**, com efeitos
verdadeiros conhecidos, gerados por `stats/gerar_dados.py` (semente fixa).
Para regenerá-los:

```bash
cd stats && python gerar_dados.py
```

### Publicar como site

Em *Settings → Pages*, escolha *Deploy from a branch*, o branch principal e a
pasta `/ (root)`. O índice ficará em
`https://cleitonfranco74.github.io/econometrics/stats/`.
