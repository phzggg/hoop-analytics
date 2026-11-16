import { useEffect, useMemo, useState } from 'react';
import { useTheme } from './hooks/theme.context';
import {
  explainDataError,
  formatGameDate,
  formatMetric,
  playerDataSource,
  type PlayerDataSource,
  type PlayerGame,
  type PlayerSummary,
} from './player-data';

type LoadState<T> =
  | { kind: 'loading' }
  | { kind: 'error'; message: string }
  | { kind: 'ready'; data: T };

export function Dashboard({ source }: { source: PlayerDataSource }) {
  const { isDark, toggleTheme } = useTheme();
  const [players, setPlayers] = useState<LoadState<PlayerSummary[]>>({ kind: 'loading' });
  const [games, setGames] = useState<LoadState<PlayerGame[]>>({ kind: 'ready', data: [] });
  const [selectedId, setSelectedId] = useState('');
  const [filter, setFilter] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [gamesAttempt, setGamesAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    source.listPlayers().then(
      (data) => { if (active) setPlayers({ kind: 'ready', data }); },
      (error: unknown) => { if (active) setPlayers({ kind: 'error', message: explainDataError(error) }); },
    );
    return () => { active = false; };
  }, [source, attempt]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    source.listGames(selectedId).then(
      (data) => { if (active) setGames({ kind: 'ready', data }); },
      (error: unknown) => { if (active) setGames({ kind: 'error', message: explainDataError(error) }); },
    );
    return () => { active = false; };
  }, [source, selectedId, gamesAttempt]);

  const visiblePlayers = useMemo(() => {
    if (players.kind !== 'ready') return [];
    const needle = filter.trim().toLocaleLowerCase('pt-BR');
    return players.data.filter((player) => player.player_name.toLocaleLowerCase('pt-BR').includes(needle));
  }, [players, filter]);
  const selected = players.kind === 'ready'
    ? players.data.find((player) => player.player_id === selectedId)
    : undefined;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-6xl px-500 py-800">
        <header className="flex flex-wrap items-center justify-between gap-400 border-b border-border pb-600">
          <div>
            <p className="text-200 font-semibold uppercase tracking-widest text-primary">Hoop Analytics / Fabric</p>
            <h1 className="mt-200 font-heading text-hero-800 font-bold">Jogadores NBA</h1>
            <p className="mt-200 text-300 text-muted-foreground">Pontos, assistências, rebotes e minutos por jogo.</p>
          </div>
          <button type="button" onClick={toggleTheme} className="rounded-lg border border-border bg-card px-400 py-200 text-300 font-semibold focus-visible:outline-2 focus-visible:outline-ring">
            {isDark ? 'Tema claro' : 'Tema escuro'}
          </button>
        </header>

        <section aria-labelledby="players-title" className="mt-800 rounded-xl border border-border bg-card p-600">
          <div className="flex flex-wrap items-end justify-between gap-400">
            <div>
              <p className="text-200 font-semibold uppercase tracking-widest text-primary">Visão geral</p>
              <h2 id="players-title" className="mt-200 font-heading text-hero-700 font-bold">Escolha um jogador</h2>
            </div>
            <label className="grid gap-100 text-300 font-semibold">
              Buscar jogador
              <input value={filter} onChange={(event) => setFilter(event.target.value)} className="rounded-lg border border-input bg-background px-300 py-200 text-300 focus-visible:outline-2 focus-visible:outline-ring" placeholder="Nome do jogador" />
            </label>
          </div>
          {players.kind === 'loading' && <p role="status" className="mt-600 text-muted-foreground">Consultando jogadores…</p>}
          {players.kind === 'error' && (
            <div role="alert" className="mt-600 rounded-lg border border-border bg-secondary p-400">
              <p>{players.message}</p>
              <button type="button" onClick={() => { setPlayers({ kind: 'loading' }); setSelectedId(''); setAttempt((value) => value + 1); }} className="mt-300 rounded-lg bg-primary px-400 py-200 text-primary-foreground focus-visible:outline-2 focus-visible:outline-ring">Tentar novamente</button>
            </div>
          )}
          {players.kind === 'ready' && visiblePlayers.length === 0 && (
            <p role="status" className="mt-600 text-muted-foreground">{players.data.length === 0 ? 'Nenhum jogador disponível.' : 'Nenhum jogador corresponde à busca.'}</p>
          )}
          {visiblePlayers.length > 0 && (
            <div className="mt-600 overflow-auto">
              <table className="w-full text-left text-300">
                <thead className="text-muted-foreground"><tr><th className="p-200">Jogador</th><th className="p-200">Jogos</th><th className="p-200">Pontos</th><th className="p-200">Pts/jogo</th><th className="p-200">Reb/jogo</th><th className="p-200">Ast/jogo</th><th className="p-200">Min/jogo</th></tr></thead>
                <tbody>
                  {visiblePlayers.map((player) => (
                    <tr key={player.player_id} className="border-t border-border">
                      <td className="p-200"><button type="button" aria-pressed={selectedId === player.player_id} onClick={() => { if (selectedId !== player.player_id) { setGames({ kind: 'loading' }); setSelectedId(player.player_id); } }} className="font-semibold text-primary underline focus-visible:outline-2 focus-visible:outline-ring">{player.player_name}</button></td>
                      <td className="p-200">{formatMetric(player.games_played, 0)}</td><td className="p-200">{formatMetric(player.total_points, 0)}</td><td className="p-200">{formatMetric(player.avg_points)}</td><td className="p-200">{formatMetric(player.avg_rebounds)}</td><td className="p-200">{formatMetric(player.avg_assists)}</td><td className="p-200">{formatMetric(player.avg_minutes)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section aria-labelledby="games-title" className="mt-600 rounded-xl border border-border bg-card p-600">
          <h2 id="games-title" className="font-heading text-500 font-semibold">{selected ? `Jogos · ${selected.player_name}` : 'Jogos do jogador'}</h2>
          {!selected && <p className="mt-300 text-300 text-muted-foreground">Selecione um jogador para ver seus jogos.</p>}
          {selected && games.kind === 'loading' && <p role="status" className="mt-300 text-muted-foreground">Consultando jogos…</p>}
          {selected && games.kind === 'error' && <div role="alert" className="mt-300"><p>{games.message}</p><button type="button" onClick={() => { setGames({ kind: 'loading' }); setGamesAttempt((value) => value + 1); }} className="mt-300 rounded-lg bg-primary px-400 py-200 text-primary-foreground focus-visible:outline-2 focus-visible:outline-ring">Tentar novamente</button></div>}
          {selected && games.kind === 'ready' && games.data.length === 0 && <p role="status" className="mt-300 text-muted-foreground">Nenhum jogo disponível para este jogador.</p>}
          {selected && games.kind === 'ready' && games.data.length > 0 && (
            <div className="mt-400 overflow-auto">
              <table className="w-full text-left text-300">
                <thead className="text-muted-foreground"><tr><th className="p-200">Data</th><th className="p-200">Time</th><th className="p-200">Pontos</th><th className="p-200">Rebotes</th><th className="p-200">Assistências</th><th className="p-200">Minutos</th></tr></thead>
                <tbody>{games.data.map((game) => <tr key={`${game.game_id}:${game.player_id}`} className="border-t border-border"><td className="p-200">{formatGameDate(game.game_date)}</td><td className="p-200">{game.team_name ?? '—'}</td><td className="p-200">{formatMetric(game.points, 0)}</td><td className="p-200">{formatMetric(game.rebounds, 0)}</td><td className="p-200">{formatMetric(game.assists, 0)}</td><td className="p-200">{formatMetric(game.minutes)}</td></tr>)}</tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

export default function App() {
  return <Dashboard source={playerDataSource} />;
}
