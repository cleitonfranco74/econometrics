# Conteúdo 6 — Diferenças em diferenças (Estatística e Econometria, PROFINIT)
# Execute a partir desta pasta (codigo/).

library(fixest)
df <- read.csv("../dados/programa_saude.csv")

# 2x2 e TWFE
feols(gasto_saude_pc ~ tratado * pos, data = df, cluster = ~municipio)
df$D <- df$tratado * df$pos
feols(gasto_saude_pc ~ D | municipio + ano, data = df, cluster = ~municipio)

# Estudo de eventos
es <- feols(gasto_saude_pc ~ i(ano, tratado, ref = 2014) | municipio + ano,
            data = df, cluster = ~municipio)
iplot(es)
wald(es, keep = "201[0-3]")    # pré-tendências

# Adoção escalonada: Callaway & Sant'Anna
# library(did)
# df$g <- ifelse(df$tratado == 1, 2015, 0)   # ano da primeira adoção (0 = nunca)
# att <- att_gt(yname = "gasto_saude_pc", tname = "ano", idname = "municipio",
#               gname = "g", data = df)
# aggte(att, type = "dynamic")
