import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Dashboard } from './App';
import {
  formatGameDate,
  formatMetric,
  playerDataSource,
  type PlayerDataSource,
} from './player-data';

describe('painel de jogadores', () => {
  it('informa que o conector de produção não está configurado', async () => {
    render(<Dashboard source={playerDataSource} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('conector de jogadores ainda não está configurado');
  });

  it('exibe falta de permissão sem divulgar o erro original', async () => {
    const source: PlayerDataSource = {
      listPlayers: vi.fn().mockRejectedValue(new Error('403 access denied: private-host')),
      listGames: vi.fn(),
    };
    render(<Dashboard source={source} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Acesso negado');
    expect(screen.queryByText(/private-host/)).not.toBeInTheDocument();
  });

  it('trata resultado vazio e ausência de correspondências', async () => {
    const source: PlayerDataSource = { listPlayers: vi.fn().mockResolvedValue([]), listGames: vi.fn() };
    render(<Dashboard source={source} />);
    expect(await screen.findByText('Nenhum jogador disponível.')).toBeInTheDocument();
  });

  it('consulta jogos do jogador selecionado e mantém valores nulos', async () => {
    // Fixture is local to this unit test, never used by the running app.
    const source: PlayerDataSource = {
      listPlayers: vi.fn().mockResolvedValue([{
        player_id: 'p1', player_name: 'Jogador teste', games_played: 1,
        total_points: 12, avg_points: 12, avg_rebounds: null, avg_assists: 3, avg_minutes: 20,
      }]),
      listGames: vi.fn().mockResolvedValue([{
        game_id: 'g1', game_date: '2026-11-10', team_id: 't1', team_name: 'Time teste',
        player_id: 'p1', player_name: 'Jogador teste', points: 12, rebounds: null,
        assists: 3, minutes: 20, updated_at: null,
      }]),
    };
    render(<Dashboard source={source} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Jogador teste' }));
    expect(await screen.findByText('10/11/2026')).toBeInTheDocument();
    expect(source.listGames).toHaveBeenCalledWith('p1');
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('formata datas e distingue zero de valor ausente', () => {
    expect(formatMetric(null)).toBe('—');
    expect(formatMetric(0)).toBe('0');
    expect(formatGameDate('2026-11-10')).toBe('10/11/2026');
  });
});
