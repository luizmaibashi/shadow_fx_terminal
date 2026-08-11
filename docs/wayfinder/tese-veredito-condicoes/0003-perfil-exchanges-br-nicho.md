---
tipo: pesquisa
status: resolvido
criado: 2026-08-10
---

# Ticket 0003: Perfil real de exchanges brasileiras pequenas/médias

## Bloqueio

A tese apontou reposicionamento como nicho "exchange brasileira pequena/média, não-enterprise" — mas isso ainda é inferência, não fato levantado. Preciso pesquisar: quantas VASPs existem/vão existir sob autorização BCB pós-fev/2026, qual a faixa de porte (não só as 2-3 grandes conhecidas), e se há evidência de que essas menores não conseguem pagar preço enterprise de Chainalysis/TRM/Elliptic (ou se isso é suposição).

## Resultado

**Fatos levantados (2026-08-10):**

1. **Capital mínimo pra ser VASP autorizada no Brasil: R$ 10,8 milhões**, calculado por modelo de negócio/risco operacional. Prazo pra pedir autorização: 30/10/2026. Fonte: [NDM Advogados — Capital social mínimo](https://ndmadvogados.com.br/artigo/capital-social-minimo-psav-e-exchange/), [VAAS — Autorização VASP BACEN 2026](https://blog.vaas.com.br/regulacao-exchanges-autorizacao-banco-central-2026).

2. **Preço real dos incumbentes:** Chainalysis US$ 50K-200K/ano (foco enterprise/governo); TRM Labs €60K-150K/ano (entrada mais acessível); Elliptic €80K-180K/ano. Fonte: [Costbench — Chainalysis Pricing 2026](https://costbench.com/software/crypto-compliance/chainalysis/), [Finconduit — Blockchain Analytics Providers Compared 2026](https://finconduit.com/resources/blockchain-analytics-providers-compared).

3. **Não achei dado do número real de VASPs autorizadas ou em processo no Brasil** — a busca não teve resultado nesse ponto específico.

**Tensão que os fatos revelam (não resolvida — vira input do Ticket 0004):** a hipótese original era "exchange pequena/média não paga preço enterprise". Mas VASP autorizada já precisa ter R$ 10,8mi de capital mínimo por lei — não é startup de garagem. US$ 50-200K/ano é 0,5%-2% desse capital: caro, mas não obviamente inviável pra quem já cruzou essa barra regulatória. A narrativa de "nicho sem orçamento" não está sustentada pelos fatos como estava formulada — pode ainda haver diferenciação real (especialização regional, preço mais competitivo, suporte em português), mas não é "eles não têm dinheiro".

## Adendo — pesquisa de reforço à justificativa corrigida (2026-08-11)

Ticket 0004 trocou a justificativa de nicho de "preço" pra "complexidade regulatória brasileira que incumbente global não prioriza". Esta pesquisa reforça (não substitui — ver ressalva no fim) essa segunda justificativa com fatos públicos.

**1. Dinamismo regulatório é real e mensurável, não impressão.** Linha do tempo confirmada: Lei 14.478/2022 (marco legal) → 4 consultas públicas em 2023-2024 (CPs 97, 109, 110, 111) → Resoluções BCB 519/520/521 publicadas em 10/11/2025 → vigência faseada (519/520 em fev/2026, disposições de capital estrangeiro da 521 só em mai/2026) → Resolução 561 (proíbe stablecoin como rail de liquidação, out/2026) → IN BCB 701/2026 → mudança de IOF sobre stablecoin (fev/2026) → prazo de adequação de 9 meses a partir de fev/2026. **7 mudanças regulatórias relevantes em ~18 meses**, não uma reforma única e estável. Fonte: [Agência Brasil](https://agenciabrasil.ebc.com.br/economia/noticia/2025-11/banco-central-estabelece-regras-para-o-mercado-de-criptoativos), [Mattos Filho](https://www.mattosfilho.com.br/unico/normas-regulamentacao-ativos-virtuais/), [Forbes — IOF sobre cripto](https://forbes.com.br/coluna/2026/02/governo-quer-taxar-criptomoedas-com-iof-o-que-isso-muda-para-o-investidor/).

**2. Nenhuma evidência pública de que Chainalysis/TRM Labs/Elliptic tratam o Brasil como mercado prioritário.** Busca dedicada por expansão/escritório/feature específica pro Brasil não achou nada — nem checagem de resolução BCB nos produtos, nem anúncio de mercado. Isso é evidência fraca (ausência não é prova de ausência — pode simplesmente não estar indexado), mas é consistente com a hipótese. Fonte: buscas "Chainalysis/TRM/Elliptic Brazil compliance feature" e "expansão mercado 2026" sem resultado relevante.

**3. Volume real que sustenta a demanda:** brasileiros declararam ~R$ 388 bilhões em criptoativos nos 3 primeiros trimestres de 2025, mais de 70% em stablecoins. Fonte: [Blue Consult — IOF stablecoin](https://blueconsult.com.br/iof-stablecoin-usdt/).

**Ressalva que a pesquisa não resolve (repetido do achado anterior, ainda vale):** nada disso confirma que uma exchange brasileira **trocaria** ferramenta atual (ou adotaria uma nova) por causa dessa especialização — isso continua sendo o "fato que derrubaria a tese" nomeado no PAVC ("empresas já terem modelo interno"), só descobrível perguntando a alguém de dentro. A pesquisa fortalece o "por que faz sentido a hipótese existir", não substitui o "será que é isso que o comprador realmente valoriza" — isso segue sendo o Ticket 0005.
