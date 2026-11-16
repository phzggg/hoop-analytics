# NBA Analytics — painel de jogadores em andamento

O painel local possui busca de jogadores, médias, pontos totais e detalhe
por jogo, além de estados de carregamento, vazio e erro. A camada de acesso
inclui consultas Rayfin somente leitura, com filtro de ID estruturado e
paginação limitada; ela ainda **não está ligada a entidades de produção**.
Por isso, o app informa "conector ... não está configurado" e não apresenta
dados sintéticos.

Em 12/11/2026, o Lakehouse `nba_lakehouse` em `YOUR_WORKSPACE` listou
`gold_espn_games` e `gold_espn_team_summary`. Não listou
`gold_espn_player_games` nem `gold_espn_player_summary`. Uma consulta ao
catálogo `INFORMATION_SCHEMA.COLUMNS` do endpoint SQL retornou zero colunas
para as duas tabelas de jogadores. A listagem de `INFORMATION_SCHEMA.TABLES`
do endpoint retornou apenas views de sistema; portanto, a exposição SQL das
tabelas também precisa ser verificada. Estes resultados são temporais.

## Conclusão necessária

1. Quando as tabelas de jogadores existirem e forem expostas no endpoint SQL,
   confirmar nomes, tipos, nulidade e dados reais com consultas read-only.
   Em particular, verificar o formato de `minutes` e dos identificadores;
   os tipos em `player-data.ts` são o contrato esperado, ainda não verificado.
2. Descobrir o conector `fabric-sqlanalytics`, declarar somente `read` e
   `auth.type: delegated`, gerar entidades a partir de metadados reais e
   fornecer as entidades de resumo e jogos a `createRayfinPlayerDataSource`.
   Não inferir chave primária da tabela pelo nome.
3. Executar testes, validação do conector e do app com um usuário autorizado.
   Publicar somente após validação ponta a ponta; não usar `--force`.

O aplicativo não cria nem modifica tabelas. Referências:
https://learn.microsoft.com/en-us/fabric/apps/connectors e
https://learn.microsoft.com/en-us/fabric/apps/deploy-app.

## Validação local em 12/11/2026

`npm run typecheck`, `npm run build`, `npm run lint` e `npm test` passaram
(55 testes). Os testes de interface e de consultas usam fixtures isoladas
apenas durante os testes; não verificam dados reais nem o conector publicado.
O catálogo instalado da CLI confirma que `fabric-sqlanalytics` permite somente
`read` e autenticação delegada. A inspeção real pela CLI respondeu
`Authentication is required`; `rayfin login status` informou que o keychain
do sistema não está disponível. O armazenamento de token em texto simples
não foi habilitado.

Não houve deploy, execução do backend, teste no navegador com autenticação ou
validação ponta a ponta. A origem de produção permanece deliberadamente
desabilitada até a descoberta das duas entidades reais.
