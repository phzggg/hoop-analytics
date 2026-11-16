import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { GameComparison } from './dashboard';
import type { Row } from './data';

const game: Row = { 'Visitante Id': '1', 'Mandante Id': '2', 'Sigla visitante': 'AWY', 'Sigla mandante': 'HME' };

describe('game comparison', () => {
  it('renders actual shooting percentages and their proportional rings', () => {
    const teams: Row[] = [
      { 'Time Id': '1', 'Arremessos convertidos': 4, 'Arremessos tentados': 10, 'Bolas de três convertidas': 1, 'Bolas de três tentadas': 4 },
      { 'Time Id': '2', 'Arremessos convertidos': 5, 'Arremessos tentados': 10, 'Bolas de três convertidas': 2, 'Bolas de três tentadas': 5 },
    ];
    const html = renderToStaticMarkup(<GameComparison game={game} teams={teams} />);
    expect(html).toContain('stroke-dasharray="40 100"');
    expect(html).toContain('stroke-dasharray="50 100"');
    expect(html).toContain('stroke-dasharray="25 100"');
    expect(html).toContain('Statistics by quarter are not available');
  });

  it('does not present zero attempts as a percentage or draw an arc', () => {
    const teams: Row[] = [
      { 'Time Id': '1', 'Lances livres convertidos': 0, 'Lances livres tentados': 0 },
      { 'Time Id': '2', 'Lances livres convertidos': 0, 'Lances livres tentados': 4 },
    ];
    const html = renderToStaticMarkup(<GameComparison game={game} teams={teams} />);
    expect(html).toContain('Percentage unavailable');
    expect(html).toContain('0 percent');
    expect(html).not.toContain('class="ring-value"');
  });

  it('dims the lower percentage and total while keeping ties and unavailable values neutral', () => {
    const teams: Row[] = [
      { 'Time Id': '1', 'Lances livres convertidos': 4, 'Lances livres tentados': 5, 'Rebotes': 30, 'Assistências': 8, 'Roubos': null },
      { 'Time Id': '2', 'Lances livres convertidos': 5, 'Lances livres tentados': 10, 'Rebotes': 40, 'Assistências': 8, 'Roubos': 2 },
    ];
    const html = renderToStaticMarkup(<GameComparison game={game} teams={teams} />);
    expect(html).toMatch(/<strong>Free throws<\/strong><span class="comparison-lower">/);
    expect(html).toContain('<strong class="comparison-lower">30</strong><span>Rebounds</span><strong class="">40</strong>');
    expect(html).toContain('<strong class="">8</strong><span>Assists</span><strong class="">8</strong>');
    expect(html).toContain('<strong class="">—</strong><span>Steals</span><strong class="">2</strong>');
    expect(html).toMatch(/<i class="comparison-lower" style="width:/);
  });
});
