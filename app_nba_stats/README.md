# Hoop Metrics — app_nba_stats

Aplicativo Rayfin para explorar dados do modelo semântico **NBA Analise Jogadores**
no workspace **YOUR_WORKSPACE**. A versão pública usa uma cópia apenas
dos campos esportivos necessários, sem exigir acesso ao modelo semântico.
O caminho de desenvolvimento autenticado usa acesso delegado ao modelo.

## Primeira entrega

- A temporada mais recente disponível é selecionada automaticamente, sem
  filtro de temporada. Quando houver mais de uma fase, a fase pode ser alterada
  na tela da liga.
- Calendário em lista ou mês nas páginas de jogos e times; a home mostra as
  listas Finished e Upcoming. Classificação geral calculada por
  aproveitamento, saldo, últimos cinco resultados e sequência de vitórias ou
  derrotas, agrupada por conferência ou liga. Não é uma classificação oficial: usa apenas os jogos disponíveis
  com placar completo e nome como desempate. A sequência é baseada na fase
  selecionada e nos resultados presentes na base; é omitida se a ordem não
  puder ser determinada ou se houver placar incompleto na sequência.
- Detalhes de partida em abas com períodos, box score, comparação de times e
  classificação atual calculada.
- Campanha, partidas e classificação de cada time; totais e participações de
  jogadores. A aba Jogadores exibe participantes da temporada/fase selecionadas
  e rankings de pontos, rebotes, assistências e aproveitamento de quadra.
- Estatísticas do time calculadas a partir de placares finais e box scores
  disponíveis, com a quantidade de jogos utilizada em cada fonte. Percentuais
  são calculados pela soma de acertos dividida pela soma de tentativas.
- Navegação contextual entre partidas, times e jogadores. A lista de jogadores
  representa a dimensão histórica da base, não os elencos atuais.
- Perfil do jogador com abas Games e Season, médias por jogo, aproveitamento
  agregado de FG/3PT, estatísticas e mapa de arremessos por partida. O mapa
  consulta diretamente o play-by-play público da ESPN no navegador, usando os
  IDs ESPN da partida e do jogador, e exclui lances livres. Filtros por período,
  tentativas não plotadas e diferenças em relação ao box score são informados.
  As coordenadas são aproximadas e podem não estar disponíveis em todos os jogos.
  Ao abrir um mapa, o navegador faz uma requisição à ESPN para a partida escolhida.
- Home Stats apresenta líderes por média e melhores atuações individuais por
  jogo, calculados sobre as participações disponíveis. O perfil exibe rankings
  relativos aos demais jogadores da base (sem mínimos de qualificação), não os
  rankings oficiais. As cores indicam terços do ranking; turnovers não recebem
  cor.
- A comparação de times em Statistics usa o box score da partida inteira;
  estatísticas completas por quarto não estão disponíveis na base.
  Informações biográficas são consultadas da ESPN ao abrir o perfil.

O pipeline diário atualiza o modelo e, após seu refresh, publica uma nova cópia
pública. O app informa a data de geração da cópia; os dados **não são ao vivo**. Jogos
agendados podem não ter placar, períodos ou estatísticas. A cobertura começa
na temporada 2026–27 e depende dos dados coletados. A lista do time é derivada
das participações e não equivale a um roster oficial. O modelo semântico atual
não fornece coordenadas por tentativa; o mapa usa dados da ESPN por partida e
não representa um agregado da temporada. A barra representa o tempo transcorrido
entre o início da temporada regular e o fim da pós-temporada informados pela
ESPN; não mede a quantidade de jogos realizados.

## Atualização pública

O pipeline `ESPN_Processar_Lotes` inicia diariamente às 03:00 no fuso
`E. South America Standard Time`. Após a conclusão bem-sucedida de
`16_ESPN_Players_Gold`, o notebook `Hoop_Public_Publish` consulta os campos
esportivos permitidos e publica a cópia no banco do app. O horário exibido
no app corresponde à geração da cópia, não ao início do pipeline.

O publicador verifica as contagens do modelo, grava os dados em partes e
confere seu conteúdo antes de registrar a versão como pronta. O app lê apenas
versões prontas, verifica quantidade e integridade e exibe erros de leitura.
Se uma execução falhar antes da publicação, a última versão completa continua
disponível. As entidades públicas permitem apenas leitura anônima; o modelo
semântico permanece privado.

As versões antigas e partes de execuções incompletas ainda não são removidas
automaticamente e ocupam espaço no banco. O agendamento existente termina em
30 de junho de 2027; deve ser renovado antes dessa data.

O código do notebook está em `scripts/publish-snapshot.py`. Para regenerar
sua definição a partir da lista de campos e consultas em `src/data.ts`:

```powershell
node scripts\build-publisher.mjs app_nba_stats <model-id> <output-ipynb>
```

Após alterar a lista de campos ou o publicador, atualize a definição do
notebook no Fabric e verifique uma execução antes de depender da nova versão.
Revise qualquer novo campo para confirmar que pode ser público.

## Desenvolvimento e publicação

Para desenvolvimento ou recuperação, é possível gerar uma cópia estática.
Com Node.js 24 e Azure CLI autenticado com acesso ao modelo, uma cópia local
dos campos esportivos usados pelo app pode ser gerada com:

```powershell
New-Item -ItemType Directory -Force local-data
node scripts\export-snapshot.mjs <workspace-id> <model-id> local-data\nba-snapshot.json
```

O exportador compara o número de linhas retornadas com o modelo e interrompe
a operação se as respostas forem incompletas ou ultrapassarem os limites da
API. O arquivo não contém tokens e não deve ser publicado sem confirmar que
todos os seus campos podem ser públicos. Para usar esse caminho,
copie o arquivo para `public\nba-snapshot.json` e defina
`VITE_PUBLIC_SNAPSHOT_URL=/nba-snapshot.json` sem `VITE_PUBLIC_DATA=true`.
O Vite inclui esse arquivo
na build; somente copie dados que podem ser
compartilhados publicamente. Em produção, `VITE_PUBLIC_DATA=true` seleciona
a cópia publicada no serviço de dados, em vez do arquivo estático.

```powershell
npm.cmd install
npm.cmd test
npm.cmd run build
npx.cmd rayfin login
npx.cmd rayfin up
npx.cmd rayfin up status
```

O conector `nba` é gerenciado por `rayfin connector` e usa
`fabric-semanticmodel` com autenticação delegada. O arquivo
`rayfin\connectors\nba\schema.ts` é gerado pelo CLI. `rayfin dev` não executa
conectores dessa categoria: valide o caminho de ponta a ponta no app publicado.
Erros de autenticação, permissão e consulta são exibidos no aplicativo.
