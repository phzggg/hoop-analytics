import { describe, expect, it } from 'vitest';
import { conference, idLiteral, periodWinner, playerRank, playerSeasonLines, queryFor, standings, teamSummary, type Row } from './data';

const game = (status: string, home: number | null, away: number | null, date = '2026-11-01'): Row => ({
  'Situação': status, 'Pontos mandante': home, 'Pontos visitante': away,
  Data: date,
  'Mandante Id': '1', Mandante: 'Home', 'Sigla mandante': 'H', 'Logo mandante': '',
  'Visitante Id': '2', Visitante: 'Away', 'Sigla visitante': 'A', 'Logo visitante': '',
});
describe('classificação calculada', () => {
  it('conta apenas partidas finalizadas com placar completo', () => {
    const result = standings([game('FINAL', 100, 90), game('SCHEDULED', null, null), game('FINAL', null, 90)]);
    expect(result.map(t => [t.name, t.wins, t.losses])).toEqual([['Home', 1, 0], ['Away', 0, 1]]);
  });
  it('desempata pelo nome e não trata empate como vitória', () => {
    expect(standings([game('FINAL', 100, 100)])).toEqual([]);
    expect(standings([game('FINAL', 100, 90, '2026-11-01'), game('FINAL', 90, 100, '2026-11-03')]).map(t => t.name)).toEqual(['Away', 'Home']);
  });
  it('calcula saldo, últimos resultados e sequência em ordem de data, ignorando agendados', () => {
    const result = standings([
      game('FINAL', 102, 90, '2026-11-03'), game('SCHEDULED', null, null, '2026-11-05'),
      game('FINAL', 90, 100, '2026-11-01'), game('FINAL', 110, 108, '2026-11-04'),
      game('FINAL', 105, 100, '2026-11-02'),
    ]);
    const home = result.find(team => team.id === '1')!;
    expect([home.pointsDiff, home.recent, home.streak]).toEqual([9, ['D', 'V', 'V', 'V'], 'V3']);
  });
  it('não inventa sequência quando um jogo finalizado é incompleto ou a ordem é ambígua', () => {
    const incomplete = standings([game('FINAL', 100, 90, '2026-11-03'), game('FINAL', null, 90, '2026-11-02')]);
    expect(incomplete.find(team => team.id === '1')?.streak).toBeNull();
    const ambiguous = standings([game('FINAL', 100, 90), game('FINAL', 90, 100)]);
    expect(ambiguous.find(team => team.id === '1')?.streak).toBeNull();
  });
});
describe('filtros DAX', () => {
  it('aceita apenas identificadores numéricos', () => {
    expect(idLiteral('401909974')).toBe('"401909974"');
    expect(() => idLiteral('1" || TRUE()')).toThrow();
    expect(() => queryFor('games', { column:'Jogador Id', id:'1' })).toThrow();
  });
  it('filtra participações por time sem permitir colunas fora da tabela', () => {
    expect(queryFor('participation', { column:'Time Id', id:'2' })).toContain("'Participações'[Time Id] = \"2\"");
    expect(() => queryFor('games', { column:'Time Id', id:'2' })).toThrow();
  });
});
describe('médias da temporada por jogador', () => {
  const participation = (playerId: string, points: number | null, made: number, attempted: number): Row => ({
    'Jogador Id': playerId,
    'Pontos brutos': points,
    'Rebotes brutos': 6,
    'Assistências brutas': 4,
    'Minutos brutos': 30,
    'Arremessos convertidos': made,
    'Arremessos tentados': attempted,
    'Bolas de três convertidas': 2,
    'Bolas de três tentadas': 4,
    'Roubos': 1,
    'Tocos': 1,
    'Perdas de bola': 2,
    'Mais menos': 3,
  });

  it('ranks ties equally and excludes players with missing statistics', () => {
    const lines = playerSeasonLines([participation('1', 20, 2, 4), participation('2', 20, 1, 4), participation('3', 10, 0, 0), participation('4', null, 0, 0)]);
    expect(playerRank(lines,'1','points')).toEqual({rank:1,total:3});
    expect(playerRank(lines,'2','points')).toEqual({rank:1,total:3});
    expect(playerRank(lines,'3','points')).toEqual({rank:3,total:3});
    expect(playerRank(lines,'4','points')).toBeNull();
    expect(playerRank(lines,'3','fieldGoalPercentage')).toBeNull();
  });
  it('highlights only a strictly winning period with both scores known', () => {
    expect(periodWinner(31, 30)).toBe(true);
    expect(periodWinner(30, 30)).toBe(false);
    expect(periodWinner(30, null)).toBe(false);
  });

  describe('conference and team statistics', () => {
    it('classifies known NBA teams and leaves unknown teams unassigned', () => {
      expect(conference('Boston Celtics')).toBe('East');
      expect(conference('LA Clippers')).toBe('West');
      expect(conference('Unknown Team')).toBeNull();
    });

    it('uses only matching completed games and calculates weighted shooting percentages', () => {
      const games: Row[] = [
        {...game('FINAL', 110, 90), 'Jogo Id':'1'},
        {...game('FINAL', 100, 105, '2026-11-02'), 'Jogo Id':'2'},
        {...game('SCHEDULED', null, null), 'Jogo Id':'3'},
      ];
      const stats: Row[] = [
        {'Jogo Id':'1','Time Id':'1','Assistências':20,'Perdas de bola':10,'Arremessos convertidos':10,'Arremessos tentados':20},
        {'Jogo Id':'2','Time Id':'1','Assistências':30,'Perdas de bola':10,'Arremessos convertidos':1,'Arremessos tentados':2},
        {'Jogo Id':'3','Time Id':'1','Assistências':99,'Perdas de bola':1,'Arremessos convertidos':1,'Arremessos tentados':1},
        {'Jogo Id':'1','Time Id':'2','Assistências':99,'Perdas de bola':1,'Arremessos convertidos':1,'Arremessos tentados':1},
      ];
      const result = teamSummary(games, stats, '1');
      expect([result.completedGames, result.statGames, result.points, result.allowed]).toEqual([2,2,105,97.5]);
      expect(result.average('Assistências')).toBe(25);
      expect(result.ratio('Assistências','Perdas de bola')).toBe(2.5);
      expect(result.ratio('Arremessos convertidos','Arremessos tentados',100)).toBe(50);
      expect(result.average('Rebotes')).toBeNull();
    });

    it('does not replace missing stats or zero attempts with invented values', () => {
      const games = [{...game('FINAL', 100, 90), 'Jogo Id':'1'}];
      const summary = teamSummary(games, [{'Jogo Id':'1','Time Id':'1','Arremessos convertidos':0,'Arremessos tentados':0}], '1');
      expect(summary.ratio('Arremessos convertidos','Arremessos tentados',100)).toBeNull();
      expect(summary.average('Assistências')).toBeNull();
    });
  });

  it('calcula médias por jogo e percentuais a partir dos totais de arremessos', () => {
    const [line] = playerSeasonLines([
      participation('10', 20, 5, 10),
      participation('10', 30, 4, 8),
    ]);
    expect(line).toMatchObject({ playerId:'10', games:2, points:25, rebounds:6, assists:4, fieldGoalPercentage:50, threePointPercentage:50 });
  });

  it('não preenche uma média quando a estatística está incompleta', () => {
    const line = playerSeasonLines([
      participation('10', 20, 5, 10),
      participation('10', null, 4, 8),
    ])[0];
    expect(line.points).toBeNull();
    expect(line.fieldGoalPercentage).toBe(50);
  });
});
