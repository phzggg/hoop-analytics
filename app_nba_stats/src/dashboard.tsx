import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, ChevronLeft, ChevronRight, Search, Shield } from 'lucide-react';
import type { AppClient } from './client';
import { conference, number, periodWinner, playerRank, playerSeasonLines, readLeagueRows, readRows, standings, teamSummary, text, type PlayerSeasonLine, type RankMetric, type Row, type Standing } from './data';
import { fetchPlayerProfile, fetchSeasonDates, seasonProgress } from './espn';
import { fetchShots } from './shots';

type Route = { page: 'league' | 'games' | 'teams' | 'players' } | { page: 'game' | 'team' | 'player'; id: string };
type Open = (route: Route) => void;
type Load<T> = { value?: T; error?: string; loading: boolean };
const errorMessage = (error: unknown) => error instanceof Error ? error.message : String(error);
const gameDate = (game: Row) => text(game, 'Data').slice(0, 10);
const date = (value: string) => {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return match ? `${match[2]}/${match[3]}/${match[1]}` : value || 'Date unavailable';
};
const stat = (row: Row, key: string) => number(row, key)?.toLocaleString('en-US') ?? '—';
const status = (game: Row) => text(game, 'Situação') === 'FINAL' ? 'Final' : text(game, 'Situação') === 'SCHEDULED' ? 'Scheduled' : text(game, 'Situação') || 'Status unavailable';
const sortGames = (games: Row[], direction: 'asc' | 'desc') => [...games].sort((a, b) => direction === 'asc'
  ? gameDate(a).localeCompare(gameDate(b)) : gameDate(b).localeCompare(gameDate(a)));

function useData<T>(key: string, fetcher: () => Promise<T>): Load<T> {
  const [state, setState] = useState<Load<T>>({ loading: true });
  useEffect(() => {
    let active = true;
    setState({ loading: true });
    fetcher().then(value => { if (active) setState({ value, loading: false }); })
      .catch(error => { if (active) setState({ error: errorMessage(error), loading: false }); });
    return () => { active = false; };
  }, [key]);
  return state;
}

function Status({ loading, error, empty, children }: { loading: boolean; error?: string; empty?: boolean; children: ReactNode }) {
  if (loading) return <div className="notice">Loading NBA data...</div>;
  if (error) return <div className="notice error" role="alert">Unable to load data: {error}</div>;
  if (empty) return <div className="notice">No data available for this selection.</div>;
  return <>{children}</>;
}

function Logo({ src, alt = '', large = false }: { src: string; alt?: string; large?: boolean }) {
  return src ? <img className={large ? 'logo large' : 'logo'} src={src} alt={alt} referrerPolicy="no-referrer" /> :
    <span className={large ? 'logo logo-placeholder large' : 'logo logo-placeholder'}><Shield size={20} /></span>;
}

export function Brand() {
  return <div className="brand"><div className="brand-mark"><svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="13" /><path d="M7 20h26M20 7v26M10.8 10.8c7 3.2 11.6 9.2 12.2 21M29.2 10.8c-5.3 2.4-9.2 6.7-11 12.2" /><path className="brand-pulse" d="M4 28h7l3-4 3 6 3-4h5" /></svg></div><div><strong>HOOP METRICS</strong><small>NBA ANALYTICS</small></div></div>;
}

export function Dashboard({ client }: { client: AppClient }) {
  const [route, setRoute] = useState<Route>({ page: 'league' });
  const [history, setHistory] = useState<Route[]>([]);
  const [phase, setPhase] = useState('');
  const [search, setSearch] = useState('');
  const [globalSearch, setGlobalSearch] = useState('');
  const gamesData = useData('games', () => readRows(client, 'games'));
  const playersData = useData('players', () => readRows(client, 'players'));
  const games = gamesData.value ?? [];
  const players = playersData.value ?? [];
  const season = useMemo(() => [...new Set(games.map(g => text(g, 'Temporada')).filter(Boolean))].sort().reverse()[0] ?? '', [games]);
  const phases = useMemo(() => [...new Set(games.filter(g => text(g, 'Temporada') === season).map(g => text(g, 'Fase')).filter(Boolean))].sort(), [games, season]);
  useEffect(() => { if (phases.length && !phases.includes(phase)) setPhase(phases.includes('Regular Season') ? 'Regular Season' : phases[0]); }, [phases, phase]);
  const filtered = games.filter(g => text(g, 'Temporada') === season && text(g, 'Fase') === phase);
  const table = standings(filtered);
  const open: Open = next => { setHistory(old => [...old, route]); setSearch(''); setRoute(next); window.scrollTo(0, 0); };
  const back = () => { setRoute(history[history.length - 1] ?? { page: 'league' }); setHistory(old => old.slice(0, -1)); window.scrollTo(0, 0); };
  const nav = [
    { page: 'league', label: 'NBA' },
    { page: 'games', label: 'Games' },
    { page: 'teams', label: 'Teams' },
    { page: 'players', label: 'Players' },
  ] as const;
  const active = route.page === 'game' ? 'games' : route.page === 'team' ? 'teams' : route.page === 'player' ? 'players' : route.page;
  return <div className="shell">
    <div className="main"><header className="topbar"><button className="brand-button" aria-label="NBA home" onClick={() => open({page:'league'})}><Brand /></button><form className="global-search" onSubmit={event => {
      event.preventDefault();
      setHistory(old => [...old, route]);
      setSearch(globalSearch.trim());
      setRoute({ page:'players' });
    }}><Search size={17} /><input value={globalSearch} onChange={event => setGlobalSearch(event.target.value)} aria-label="Search players" placeholder="Search players..." /><button type="submit">Search</button></form></header>
      <main className="content">{'snapshot' in client && <p className="snapshot-freshness">Data snapshot: {new Date(client.snapshot.generatedAt).toLocaleString('en-US', { dateStyle:'medium', timeStyle:'short' })} · {client.scheduled ? 'Daily refresh scheduled' : 'Updates are not automatic'}</p>}<div className="breadcrumb">{route.page !== 'league' && <button className="back" onClick={back}><ArrowLeft size={15} /> Back</button>}<span>Basketball</span><ChevronRight size={14} /><strong>{nav.find(n => n.page === active)?.label}</strong></div>
      <Status loading={gamesData.loading || playersData.loading} error={gamesData.error || playersData.error} empty={!games.length}>
        {route.page === 'league' && <League games={filtered} players={players} client={client} standingsRows={table} season={season} phase={phase} phases={phases} setPhase={setPhase} open={open} />}
        {route.page === 'games' && <><PageHeader eyebrow="NBA · GAMES" title="Schedule" subtitle={`${season} · available results and upcoming games`} /><div className="single-panel"><GamesPanel games={filtered} open={open} expanded /></div></>}
        {route.page === 'teams' && <><PageHeader eyebrow="NBA · TEAMS" title="Standings" subtitle={`${season} · ${phaseLabel(phase)}`} /><section className="card"><StandingsView rows={table} open={open} /></section></>}
        {route.page === 'players' && <><PageHeader eyebrow="NBA · PLAYERS" title="Players" subtitle="Players in the dataset; this is not a current roster." /><section className="card"><div className="search"><Search size={17} /><input placeholder="Search players" value={search} onChange={e => setSearch(e.target.value)} aria-label="Search players" /></div><div className="player-grid">{players.filter(p => text(p, 'Jogador').toLowerCase().includes(search.toLowerCase())).sort((a,b) => text(a,'Jogador').localeCompare(text(b,'Jogador'))).map(p => <button className="player-item" key={text(p, 'Jogador Id')} onClick={() => open({ page: 'player', id: text(p, 'Jogador Id') })}><Logo src={text(p,'Foto')} /><span><strong>{text(p,'Jogador')}</strong><small>{text(p,'Posição') || 'Position unavailable'}</small></span><ArrowRight size={15} /></button>)}</div></section></>}
        {route.page === 'game' && <GameDetail id={route.id} games={filtered} players={players} rows={table} client={client} open={open} />}
        {route.page === 'team' && <TeamDetail id={route.id} games={filtered} rows={table} season={season} phase={phase} players={players} client={client} open={open} />}
        {route.page === 'player' && <PlayerDetail key={route.id} id={route.id} players={players} games={filtered} season={season} phase={phase} client={client} open={open} />}
      </Status></main></div></div>;
}

function phaseLabel(phase: string) {
  return phase;
}

function PageHeader({ eyebrow, title, subtitle, icon }: { eyebrow: string; title: string; subtitle: string; icon?: ReactNode }) {
  return <div className="page-header">{icon && <div className="header-icon">{icon}</div>}<div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{subtitle}</p></div></div>;
}

function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (value: T) => void; items: { value: T; label: string }[] }) {
  const index = Math.max(0, items.findIndex(item => item.value === value));
  return <div className="tabs" role="tablist"><div className="tabs-inner">{items.map(item => <button role="tab" aria-selected={value === item.value} className={value === item.value ? 'tab active' : 'tab'} key={item.value} onClick={() => onChange(item.value)}>{item.label}</button>)}<span className="tab-indicator" aria-hidden="true" style={{width:`${100 / items.length}%`, transform:`translateX(${index * 100}%)`}} /></div></div>;
}

function Segmented<T extends string>({value, onChange, items, className = ''}: {value: T; onChange: (value: T) => void; items: {value: T; label: string}[]; className?: string}) {
  const index = Math.max(0, items.findIndex(item => item.value === value));
  return <div className={`segmented ${className}`}><span className="segmented-indicator" aria-hidden="true" style={{width:`calc((100% - 6px) / ${items.length})`, transform:`translateX(${index * 100}%)`}} />{items.map(item => <button key={item.value} aria-pressed={value === item.value} className={value === item.value ? 'selected' : ''} onClick={() => onChange(item.value)}>{item.label}</button>)}</div>;
}

function League({ games, players, client, standingsRows, season, phase, phases, setPhase, open }: { games: Row[]; players: Row[]; client: AppClient; standingsRows: Standing[]; season: string; phase: string; phases: string[]; setPhase: (phase: string) => void; open: Open }) {
  const [tab, setTab] = useState<'standings' | 'stats' | 'overview'>('standings');
  const featured = sortGames(games.filter(g => text(g,'Situação') === 'FINAL'), 'desc')[0] ?? sortGames(games, 'asc')[0];
  return <><section className="card league-hero"><div className="league-hero-identity"><img className="nba-badge" src="https://a.espncdn.com/i/teamlogos/leagues/500/nba.png" alt="NBA logo" referrerPolicy="no-referrer" /><div><span className="eyebrow">BASKETBALL · USA</span><h1>NBA</h1><p>{season} · {phaseLabel(phase)}</p>{phases.length > 1 && <label className="phase-label">Phase<select value={phase} onChange={e => setPhase(e.target.value)}>{phases.map(p => <option key={p} value={p}>{phaseLabel(p)}</option>)}</select></label>}</div></div><SeasonTimeline season={season} /></section>
    <div className="workspace-grid"><div className="left-column">
      {featured && <section className="card featured"><div className="card-title"><h2>Featured</h2><span>LATEST AVAILABLE</span></div><div className="featured-date">{date(gameDate(featured))} · {status(featured)}</div><button className="featured-match" onClick={() => open({ page:'game', id:text(featured,'Jogo Id') })}><span><Logo large src={text(featured,'Logo visitante')} /><strong>{text(featured,'Sigla visitante')}</strong></span><b>{stat(featured,'Pontos visitante')} <i>–</i> {stat(featured,'Pontos mandante')}</b><span><Logo large src={text(featured,'Logo mandante')} /><strong>{text(featured,'Sigla mandante')}</strong></span></button><button className="subtle-link" onClick={() => open({ page:'game', id:text(featured,'Jogo Id') })}>View game <ArrowRight size={13} /></button></section>}
      <GamesPanel games={games} open={open} listOnly />
    </div><section className="card main-panel"><Tabs value={tab} onChange={setTab} items={[{value:'standings',label:'Standings'}, {value:'stats',label:'Stats'}, {value:'overview',label:'Overview'}]} />
      {tab === 'standings' && <StandingsView rows={standingsRows} open={open} />}
      {tab === 'stats' && <LeagueStats client={client} players={players} games={games} season={season} phase={phase} open={open} />}
      {tab === 'overview' && <div className="overview"><div className="overview-cards"><Metric label="Finished games" value={games.filter(g => text(g,'Situação') === 'FINAL').length} /><Metric label="Scheduled games" value={games.filter(g => text(g,'Situação') === 'SCHEDULED').length} /><Metric label="Teams with results" value={standingsRows.length} /></div><h2>Explore the season</h2><p>Select a game or team to explore the available history.</p><button className="primary" onClick={() => open({page:'games'})}>View schedule <ArrowRight size={15} /></button></div>}
    </section></div></>;
}

function SeasonTimeline({ season }: { season: string }) {
  const data = useData(`season-dates-${season}`, () => fetchSeasonDates(season));
  if (data.loading) return <div className="timeline-status">Loading season dates...</div>;
  if (data.error || !data.value) return <div className="timeline-status error">Season timeline unavailable: {data.error}</div>;
  const {start, end} = data.value;
  const progress = seasonProgress(start, end, Date.now());
  const label = (value: string) => new Intl.DateTimeFormat('en-US', {month:'short',day:'numeric',timeZone:'UTC'}).format(new Date(value));
  return <div className="season-progress"><div className="progress-caption"><strong>Season timeline</strong><span>Regular season through postseason · ESPN</span></div><div className="progress-track" role="progressbar" aria-label="Elapsed season timeline" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress)}><span style={{width:`${progress}%`}} /></div><div className="timeline-dates"><span>{label(start)}</span><span>{label(end)}</span></div></div>;
}

function Metric({ label, value }: { label: string; value: number | null }) {
  return <div className="metric"><span>{label}</span><strong>{value?.toLocaleString('en-US') ?? '—'}</strong></div>;
}

function LeagueStats({client, players, games, season, phase, open}: {client: AppClient; players: Row[]; games: Row[]; season: string; phase: string; open: Open}) {
  const [metric, setMetric] = useState<'points' | 'rebounds' | 'assists'>('points');
  const [gameMetric, setGameMetric] = useState('Pontos brutos');
  const data = useData(`league-stats-${season}-${phase}`, () => readLeagueRows(client, season, phase));
  const rows = data.value ?? [];
  const leaders = playerSeasonLines(rows).filter(line => line[metric] !== null).sort((a,b) => (b[metric] ?? 0) - (a[metric] ?? 0) || a.playerId.localeCompare(b.playerId)).slice(0,5);
  const bestGames = [...rows].filter(row => number(row,gameMetric) !== null).sort((a,b) => (number(b,gameMetric) ?? 0) - (number(a,gameMetric) ?? 0) || text(b,'Data do jogo').localeCompare(text(a,'Data do jogo'))).slice(0,5);
  return <Status loading={data.loading} error={data.error}><p className="coverage-note">Based on available {season} {phaseLabel(phase)} appearances. Unqualified rankings; not official NBA leaders.</p><div className="league-leaders"><section><h2>Top players</h2><label className="stat-picker">Statistic <select value={metric} onChange={event => setMetric(event.target.value as typeof metric)}><option value="points">Points per game</option><option value="rebounds">Rebounds per game</option><option value="assists">Assists per game</option></select></label>{leaders.length ? leaders.map((line,index) => {
    const player = players.find(item => text(item,'Jogador Id') === line.playerId);
    return <button className="leader-row" key={line.playerId} disabled={!player} onClick={() => open({page:'player',id:line.playerId})}><span className="leader-rank">{index+1}</span><Logo src={text(player ?? {},'Foto')} /><span className="leader-player"><strong>{text(player ?? {},'Jogador') || `Player ${line.playerId}`}</strong><small>{line.games} GP · {text(player ?? {},'Posição') || 'Position unavailable'}</small></span><b>{average(line[metric])}</b></button>;
  }) : <div className="notice">No statistics available.</div>}</section><section><h2>Top game performances</h2><label className="stat-picker">Statistic <select value={gameMetric} onChange={event => setGameMetric(event.target.value)}><option value="Pontos brutos">Points</option><option value="Rebotes brutos">Rebounds</option><option value="Assistências brutas">Assists</option></select></label>{bestGames.length ? bestGames.map((row,index) => {
    const player = players.find(item => text(item,'Jogador Id') === text(row,'Jogador Id'));
    const game = games.find(item => text(item,'Jogo Id') === text(row,'Jogo Id'));
    return <button className="leader-row" key={`${text(row,'Jogo Id')}-${text(row,'Jogador Id')}`} disabled={!game} onClick={() => open({page:'game',id:text(row,'Jogo Id')})}><span className="leader-rank">{index+1}</span><Logo src={text(player ?? {},'Foto')} /><span className="leader-player"><strong>{text(player ?? {},'Jogador') || `Player ${text(row,'Jogador Id')}`}</strong><small>{game ? `${text(game,'Sigla visitante')} ${stat(game,'Pontos visitante')} – ${stat(game,'Pontos mandante')} ${text(game,'Sigla mandante')}` : date(text(row,'Data do jogo'))}</small></span><b>{stat(row,gameMetric)}</b></button>;
  }) : <div className="notice">No game statistics available.</div>}</section></div></Status>;
}

function StandingsView({ rows, open }: { rows: Standing[]; open: Open }) {
  const [view, setView] = useState<'conferences' | 'league'>('conferences');
  const east = rows.filter(row => conference(row.name) === 'East');
  const west = rows.filter(row => conference(row.name) === 'West');
  const unknown = rows.filter(row => !conference(row.name));
  return <><Segmented className="standings-switch" value={view} onChange={setView} items={[{value:'conferences',label:'Conferences'}, {value:'league',label:'League'}]} />
    <div className="standings-note">Calculated from available final scores; alphabetical tie-breaker, not official NBA standings.</div>
    {view === 'league' ? <><h2 className="standings-heading">League</h2><StandingsTable rows={rows} open={open} /></> : <>{[{name:'Eastern Conference', rows:east}, {name:'Western Conference', rows:west}, ...(unknown.length ? [{name:'Conference unavailable',rows:unknown}] : [])].map(group => <section key={group.name}><h2 className="standings-heading">{group.name}</h2><StandingsTable rows={group.rows} open={open} /></section>)}</>}
  </>;
}

function StandingsTable({ rows, open, highlight = [] }: { rows: Standing[]; open: Open; highlight?: string[] }) {
  if (!rows.length) return <div className="notice">No completed results available.</div>;
  const leader = rows[0];
  return <div className="table-scroll"><table className="standings"><thead><tr><th>#</th><th>TEAM</th><th>P</th><th>W</th><th>L</th><th>PCT</th><th>GB</th><th>DIFF</th><th>LAST 5</th><th>STR</th></tr></thead><tbody>{rows.map((team,i) => {
    const gb = ((leader.wins - team.wins) + (team.losses - leader.losses)) / 2;
    return <tr key={team.id} className={highlight.includes(team.id) ? 'highlight' : ''}><td>{i+1}</td><td><button className="team-link" onClick={() => open({ page:'team', id:team.id })}><Logo src={team.logo} />{team.name}</button></td><td>{team.wins+team.losses}</td><td>{team.wins}</td><td>{team.losses}</td><td>{(team.wins/(team.wins+team.losses)).toFixed(3)}</td><td>{gb === 0 ? '—' : gb.toFixed(1)}</td><td>{team.pointsDiff > 0 ? '+' : ''}{team.pointsDiff}</td><td><span className="form" aria-label={`Last results: ${team.recent.map(result => result === 'V' ? 'W' : 'L').join(', ') || 'unavailable'}`}>{team.recent.map((result,index) => <span className={result === 'V' ? 'win' : 'loss'} key={index}>{result === 'V' ? 'W' : 'L'}</span>)}{!team.recent.length && '—'}</span></td><td>{team.streak?.replace(/^V/, 'W').replace(/^D/, 'L') ?? '—'}</td></tr>;
  })}</tbody></table></div>;
}

function GamesPanel({ games, open, expanded = false, teamId, listOnly = false }: { games: Row[]; open: Open; expanded?: boolean; teamId?: string; listOnly?: boolean }) {
  const [mode, setMode] = useState<'list' | 'calendar'>('list');
  const [type, setType] = useState<'finished' | 'upcoming'>('finished');
  const [page, setPage] = useState(0);
  const [month, setMonth] = useState('');
  const matching = sortGames(games.filter(g => text(g,'Situação') === (type === 'finished' ? 'FINAL' : 'SCHEDULED')), type === 'finished' ? 'desc' : 'asc');
  const months = [...new Set(games.map(gameDate).filter(d => /^\d{4}-\d{2}-\d{2}$/.test(d)).map(d => d.slice(0,7)))].sort();
  const currentMonth = months.includes(month) ? month : (matching[0] ? gameDate(matching[0]).slice(0,7) : months[months.length - 1] ?? '');
  const size = expanded ? 18 : 8;
  const maxPage = Math.max(0, Math.ceil(matching.length / size) - 1);
  const currentPage = Math.min(page, maxPage);
  const changeType = (next: 'finished' | 'upcoming') => { setType(next); setPage(0); };
  return <section className="card games-panel"><div className="card-title"><h2>Games</h2><span>NBA</span></div>
    {!listOnly && <Segmented value={mode} onChange={setMode} items={[{value:'list',label:'List'}, {value:'calendar',label:'Calendar'}]} />}
    {mode === 'list' ? <><div className="games-controls"><Segmented className="compact" value={type} onChange={changeType} items={[{value:'finished',label:'Finished'}, {value:'upcoming',label:'Upcoming'}]} /><div className="pager"><button aria-label="Previous page" disabled={currentPage === 0} onClick={() => setPage(currentPage-1)}><ChevronLeft size={16} /></button><button aria-label="Next page" disabled={currentPage >= maxPage} onClick={() => setPage(currentPage+1)}><ChevronRight size={16} /></button></div></div>
      <div className="league-label"><span className="league-mark">NBA</span><span>NBA<small>{matching.length} available games</small></span></div><GameList games={matching.slice(currentPage*size, (currentPage+1)*size)} open={open} teamId={teamId} /></> :
      <Calendar games={games} month={currentMonth} months={months} setMonth={setMonth} open={open} teamId={teamId} />}
  </section>;
}

function Calendar({ games, month, months, setMonth, open, teamId }: { games: Row[]; month: string; months: string[]; setMonth: (month: string) => void; open: Open; teamId?: string }) {
  const [selected, setSelected] = useState('');
  if (!month) return <div className="notice">No dates available.</div>;
  const [year, monthNumber] = month.split('-').map(Number);
  const firstDay = new Date(Date.UTC(year, monthNumber - 1, 1)).getUTCDay();
  const days = new Date(Date.UTC(year, monthNumber, 0)).getUTCDate();
  const label = new Intl.DateTimeFormat('en-US', { month:'long', year:'numeric', timeZone:'UTC' }).format(new Date(Date.UTC(year, monthNumber - 1, 1)));
  const index = months.indexOf(month);
  const visibleDate = selected.startsWith(month) ? selected : '';
  return <><div className="month-nav"><button aria-label="Previous month" disabled={index <= 0} onClick={() => setMonth(months[index-1])}><ChevronLeft size={17} /></button><strong>{label}</strong><button aria-label="Next month" disabled={index >= months.length-1} onClick={() => setMonth(months[index+1])}><ChevronRight size={17} /></button></div>
    <div className="calendar">{['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map((day,i) => <span className="week-day" key={i}>{day}</span>)}{Array.from({ length:firstDay }, (_,i) => <span key={`empty-${i}`} />)}{Array.from({ length:days }, (_,i) => {
      const day = `${month}-${String(i+1).padStart(2,'0')}`;
      const dayGames = games.filter(game => gameDate(game) === day);
      const game = dayGames[0];
      if (teamId && game) {
        const home = text(game,'Mandante Id') === teamId;
        const teamScore = number(game, home ? 'Pontos mandante' : 'Pontos visitante');
        const opponentScore = number(game, home ? 'Pontos visitante' : 'Pontos mandante');
        const finished = text(game,'Situação') === 'FINAL';
        const result = finished && teamScore !== null && opponentScore !== null && teamScore !== opponentScore
          ? teamScore > opponentScore ? 'W' : 'L' : '';
        const opponentLogo = text(game, home ? 'Logo visitante' : 'Logo mandante');
        const opponentName = text(game, home ? 'Visitante' : 'Mandante');
        const opponentAbbreviation = text(game, home ? 'Sigla visitante' : 'Sigla mandante');
        const scoreLabel = finished && teamScore !== null && opponentScore !== null
          ? `${teamScore}–${opponentScore}` : text(game,'Situação') === 'SCHEDULED' ? 'TBD' : '—';
        const className = `calendar-day team-game-day ${home ? 'home' : 'away'}${visibleDate === day ? ' chosen' : ''}`;
        return <button key={day} className={className} aria-label={`${date(day)}: ${home ? 'home' : 'away'} against ${opponentName}, ${status(game)} ${result} ${scoreLabel}${dayGames.length > 1 ? `, ${dayGames.length} games` : ''}`} onClick={() => setSelected(day)}>
          <span className="calendar-date">{i+1}{dayGames.length > 1 ? ` +${dayGames.length-1}` : ''}</span><span className="calendar-opponent"><Logo src={opponentLogo} /><small>{opponentAbbreviation || opponentName}</small></span><strong className={`calendar-score ${result === 'W' ? 'team-win' : result === 'L' ? 'team-loss' : ''}`}>{scoreLabel}</strong>
        </button>;
      }
      return <button key={day} disabled={!dayGames.length} className={visibleDate === day ? 'calendar-day chosen' : 'calendar-day'} onClick={() => setSelected(day)}><span>{i+1}</span>{dayGames.length > 0 && <small>{dayGames.length} {dayGames.length === 1 ? 'game' : 'games'}</small>}</button>;
    })}</div>{teamId && <div className="calendar-legend"><span><i className="home-key" />Home</span><span><i className="away-key" />Away</span></div>}{visibleDate ? <><div className="league-label">{date(visibleDate)}</div><GameList games={games.filter(g => gameDate(g) === visibleDate)} open={open} teamId={teamId} /></> : <div className="calendar-help">Select a date to view games.</div>}</>;
}

function GameList({ games, open, teamId }: { games: Row[]; open: Open; teamId?: string }) {
  if (!games.length) return <div className="notice">No games available.</div>;
  return <div className="game-list">{games.map(game => {
    const home = number(game,'Pontos mandante'); const away = number(game,'Pontos visitante');
    const final = text(game,'Situação') === 'FINAL' && home !== null && away !== null && home !== away;
    const homeWon = final ? home > away : false;
    const awayWon = final ? away > home : false;
    const result = teamId && final
      ? ((text(game,'Mandante Id') === teamId ? homeWon : awayWon) ? 'W' : 'L') : null;
    return <button className="game-row" key={text(game,'Jogo Id')} onClick={() => open({ page:'game', id:text(game,'Jogo Id') })}>
      <span className="game-date">{date(gameDate(game)).slice(0,5)}<small>{status(game)}</small></span><span className="matchup"><span className={awayWon ? 'winner' : ''}><Logo src={text(game,'Logo visitante')} />{text(game,'Visitante')}</span><span className={homeWon ? 'winner' : ''}><Logo src={text(game,'Logo mandante')} />{text(game,'Mandante')}</span></span><span className="scores"><strong className={awayWon ? 'winner' : ''}>{stat(game,'Pontos visitante')}</strong><strong className={homeWon ? 'winner' : ''}>{stat(game,'Pontos mandante')}</strong></span>{result && <span className={`result ${result === 'W' ? 'win' : 'loss'}`}>{result}</span>}
    </button>;
  })}</div>;
}

function GameDetail({ id, games, players, rows, client, open }: { id: string; games: Row[]; players: Row[]; rows: Standing[]; client: AppClient; open: Open }) {
  const [tab, setTab] = useState<'box' | 'stats' | 'standings'>('box');
  const [teamFilter, setTeamFilter] = useState('all');
  const data = useData(`game-${id}`, () => Promise.all([
    readRows(client, 'participation', { column:'Jogo Id', id }),
    readRows(client, 'teamStats', { column:'Jogo Id', id }),
    readRows(client, 'periods', { column:'Jogo Id', id }),
  ]));
  const game = games.find(g => text(g,'Jogo Id') === id);
  if (!game) return <div className="notice error">Game not found in this phase.</div>;
  const [participation, teams, unsortedPeriods] = data.value ?? [[], [], []];
  const periods = [...unsortedPeriods].sort((a,b) => (number(a,'Período') ?? 0) - (number(b,'Período') ?? 0));
  const awayId = text(game,'Visitante Id'); const homeId = text(game,'Mandante Id');
  const labels = [...new Set(periods.map(p => text(p,'Descrição do período')))];
  return <><section className="card match-header"><div className="match-score">{(['visitante', 'mandante'] as const).map(side => <button key={side} onClick={() => open({ page:'team', id:text(game, side === 'mandante' ? 'Mandante Id' : 'Visitante Id') })}><Logo large src={text(game,`Logo ${side}`)} /><strong>{text(game,side === 'mandante' ? 'Mandante' : 'Visitante')}</strong><small>{side === 'mandante' ? 'Home' : 'Away'}</small></button>)}<span className="score-value">{stat(game,'Pontos visitante')} <i>–</i> {stat(game,'Pontos mandante')}<small>{status(game)}</small></span></div><div className="match-meta"><CalendarDays size={14} /> {date(gameDate(game))} <span>·</span> NBA <span>·</span> {phaseLabel(text(game,'Fase'))}</div></section>
    <Status loading={data.loading} error={data.error}><div className="workspace-grid detail-layout"><div className="left-column"><section className="card periods"><div className="card-title"><h2>By period</h2><span>POINTS</span></div>{periods.length ? <div className="table-scroll"><table><thead><tr><th>TEAM</th>{labels.map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{[awayId,homeId].map(team => <tr key={team}><td>{text(game,team === homeId ? 'Sigla mandante' : 'Sigla visitante')}</td>{labels.map(label => {
      const current = periods.find(p => text(p,'Time Id') === team && text(p,'Descrição do período') === label) ?? {};
      const other = periods.find(p => text(p,'Time Id') === (team === homeId ? awayId : homeId) && text(p,'Descrição do período') === label) ?? {};
      const won = text(game,'Situação') === 'FINAL' && periodWinner(number(current,'Pontos no período'),number(other,'Pontos no período'));
      return <td key={label} className={won ? 'period-winner' : ''}>{stat(current,'Pontos no período')}</td>;
    })}</tr>)}</tbody></table></div> : <div className="notice">Period scores are not available.</div>}</section>
      <section className="card"><div className="card-title"><h2>About the game</h2></div><div className="fact-list"><span>Competition<strong>NBA</strong></span><span>Date<strong>{date(gameDate(game))}</strong></span><span>Status<strong>{status(game)}</strong></span><span>Updates<strong>{'snapshot' in client ? 'Snapshot' : 'Daily'}</strong></span></div></section></div>
      <section className="card main-panel"><Tabs value={tab} onChange={setTab} items={[{value:'box',label:'Box score'}, {value:'stats',label:'Statistics'}, {value:'standings',label:'Standings'}]} />
        {tab === 'box' && <><div className="filter-pills team-filter">{[awayId,'all',homeId].map(teamId => <button key={teamId} aria-label={teamId === 'all' ? 'Both teams' : text(game,teamId === homeId ? 'Mandante' : 'Visitante')} aria-pressed={teamFilter === teamId} className={teamFilter === teamId ? 'selected' : ''} onClick={() => setTeamFilter(teamId)}>{teamId !== homeId && <Logo src={text(game,'Logo visitante')} />}{teamId === 'all' && <span>+</span>}{teamId !== awayId && <Logo src={text(game,'Logo mandante')} />}</button>)}</div><PlayerTable rows={participation.filter(p => teamFilter === 'all' || text(p,'Time Id') === teamFilter)} players={players} open={open} /></>}
        {tab === 'stats' && <GameComparison game={game} teams={teams} />}
        {tab === 'standings' && <><div className="panel-heading"><div><h2>League standings</h2><p>Calculated from currently available games.</p></div></div><StandingsTable rows={rows} open={open} highlight={[awayId,homeId]} /></>}
      </section></div></Status></>;
}

export function GameComparison({game, teams}: {game: Row; teams: Row[]}) {
  const away = teams.find(row => text(row,'Time Id') === text(game,'Visitante Id'));
  const home = teams.find(row => text(row,'Time Id') === text(game,'Mandante Id'));
  if (!away || !home) return <div className="notice">Team comparison is unavailable for this game.</div>;
  const shooting = [
    {label:'Free throws',made:'Lances livres convertidos',attempted:'Lances livres tentados'},
    {label:'Field goals',made:'Arremessos convertidos',attempted:'Arremessos tentados'},
    {label:'Three-pointers',made:'Bolas de três convertidas',attempted:'Bolas de três tentadas'},
    {label:'Two-pointers',made:'Arremessos convertidos',attempted:'Arremessos tentados'},
  ];
  return <div className="comparison"><div className="comparison-heading"><h2>Game statistics</h2><div className="comparison-teams"><span><Logo src={text(game,'Logo visitante')} />{text(game,'Sigla visitante')}</span><span className="comparison-period">Full game</span><span>{text(game,'Sigla mandante')}<Logo src={text(game,'Logo mandante')} /></span></div><p>Full-game box score. Statistics by quarter are not available. Higher values are highlighted, not necessarily better performance.</p></div><div className="comparison-grid"><section><h3>Shooting</h3>{shooting.map(item => {
    const format = (row: Row) => {
      let made = number(row,item.made), attempts = number(row,item.attempted);
      if (item.label === 'Two-pointers') {
        const threeMade = number(row,'Bolas de três convertidas'), threeAttempts = number(row,'Bolas de três tentadas');
        made = made !== null && threeMade !== null && made >= threeMade ? made - threeMade : null;
        attempts = attempts !== null && threeAttempts !== null && attempts >= threeAttempts ? attempts - threeAttempts : null;
      }
      const percent = made !== null && attempts !== null && made >= 0 && attempts > 0 && made <= attempts ? 100 * made / attempts : null;
      return {display: `${made ?? '—'}/${attempts ?? '—'}`, percent};
    };
    const a = format(away), h = format(home);
    return <div className="shooting-comparison" key={item.label}><span className={lowerValue(a.percent,h.percent) ? 'comparison-lower' : ''}>{a.display}<ShootingRing value={a.percent} side="away" /></span><strong>{item.label}</strong><span className={lowerValue(h.percent,a.percent) ? 'comparison-lower' : ''}><ShootingRing value={h.percent} side="home" />{h.display}</span></div>;
  })}</section><section><h3>Game totals</h3>{[['Rebotes','Rebounds'],['Assistências','Assists'],['Perdas de bola','Turnovers'],['Roubos','Steals'],['Tocos','Blocks']].map(([key,label]) => {
    const a = number(away,key), h = number(home,key), total = a !== null && h !== null ? a + h : null;
    return <div className="comparison-stat" key={key}><div><strong className={lowerValue(a,h) ? 'comparison-lower' : ''}>{a ?? '—'}</strong><span>{label}</span><strong className={lowerValue(h,a) ? 'comparison-lower' : ''}>{h ?? '—'}</strong></div>{total !== null && total > 0 && <div className="comparison-bar" aria-hidden="true"><i className={lowerValue(a,h) ? 'comparison-lower' : ''} style={{width:`${100*a!/total}%`}} /><b className={lowerValue(h,a) ? 'comparison-lower' : ''} style={{width:`${100*h!/total}%`}} /></div>}</div>;
  })}</section></div></div>;
}

function lowerValue(value: number | null, other: number | null) {
  return value !== null && other !== null && value < other;
}

function ShootingRing({value, side}: {value: number | null; side: 'away' | 'home'}) {
  return <span className={`shooting-ring ${side}`} aria-label={value === null ? 'Percentage unavailable' : `${value.toFixed(0)} percent`}><svg viewBox="0 0 42 42" aria-hidden="true"><circle className="ring-track" cx="21" cy="21" r="18" />{value !== null && value > 0 && <circle className="ring-value" cx="21" cy="21" r="18" pathLength="100" strokeDasharray={`${value} 100`} />}</svg><b>{value === null ? '—' : `${value.toFixed(0)}%`}</b></span>;
}

function PlayerTable({ rows, players, open }: { rows: Row[]; players: Row[]; open: Open }) {
  if (!rows.length) return <div className="notice">No player appearances available.</div>;
  return <div className="table-scroll"><table className="box-table"><thead><tr><th>PLAYER</th><th>TEAM</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>TO</th><th>FG</th><th>3PT</th><th>+/-</th></tr></thead><tbody>{[...rows].sort((a,b) => (number(b,'Pontos brutos') ?? -1) - (number(a,'Pontos brutos') ?? -1)).map((r,i) => {
    const player = players.find(p => text(p,'Jogador Id') === text(r,'Jogador Id')) ?? {};
    return <tr key={`${text(r,'Jogador Id')}-${i}`}><td><button className="team-link player-link" onClick={() => open({ page:'player', id:text(r,'Jogador Id') })}><Logo src={text(player,'Foto')} /><span>{text(player,'Jogador') || `Player ${text(r,'Jogador Id')}`}<small>{text(player,'Posição')}</small></span></button></td><td><button className="inline-link" onClick={() => open({ page:'team', id:text(r,'Time Id') })}>{text(r,'Time')}</button></td><td>{stat(r,'Minutos brutos')}</td><td>{stat(r,'Pontos brutos')}</td><td>{stat(r,'Rebotes brutos')}</td><td>{stat(r,'Assistências brutas')}</td><td>{stat(r,'Roubos')}</td><td>{stat(r,'Tocos')}</td><td>{stat(r,'Perdas de bola')}</td><td>{stat(r,'Arremessos convertidos')}/{stat(r,'Arremessos tentados')}</td><td>{stat(r,'Bolas de três convertidas')}/{stat(r,'Bolas de três tentadas')}</td><td>{stat(r,'Mais menos')}</td></tr>;
  })}</tbody></table></div>;
}

function TeamDetail({ id, games, rows, season, phase, players, client, open }: { id: string; games: Row[]; rows: Standing[]; season: string; phase: string; players: Row[]; client: AppClient; open: Open }) {
  const [tab, setTab] = useState<'standings' | 'overview' | 'players'>('standings');
  const [playerView, setPlayerView] = useState<'general' | 'top'>('general');
  const playerData = useData(`team-players-${id}`, () => readRows(client, 'participation', { column:'Time Id', id }));
  const teamGames = games.filter(g => text(g,'Mandante Id') === id || text(g,'Visitante Id') === id);
  const sample = teamGames[0];
  if (!sample) return <div className="notice">This team has no games in the selected phase.</div>;
  const home = text(sample,'Mandante Id') === id;
  const name = text(sample, home ? 'Mandante' : 'Visitante');
  const standing = rows.find(t => t.id === id);
  const previous = sortGames(teamGames.filter(g => text(g,'Situação') === 'FINAL'), 'desc')[0];
  const next = sortGames(teamGames.filter(g => text(g,'Situação') === 'SCHEDULED'), 'asc')[0];
  return <><section className="card team-header"><div className="team-identity"><Logo large src={text(sample,home ? 'Logo mandante' : 'Logo visitante')} /><div><span className="eyebrow">NBA · TEAM</span><h1>{name}</h1><p>{season} · available record: {standing ? `${standing.wins}W – ${standing.losses}L` : 'no results'}</p></div></div><div className="adjacent-games">{previous && <MiniGame label="Previous game" game={previous} open={open} />}{next && <MiniGame label="Next available game" game={next} open={open} />}</div></section>
    <div className="workspace-grid"><div className="left-column"><GamesPanel games={teamGames} open={open} teamId={id} /></div><section className="card main-panel">
      <Tabs value={tab} onChange={setTab} items={[{value:'standings',label:'Standings'}, {value:'overview',label:'Statistics'}, {value:'players',label:'Players'}]} />
      {tab === 'standings' && <><div className="panel-heading"><div><h2>League standings</h2><p>Team highlighted in the calculated table.</p></div></div><StandingsTable rows={rows} open={open} highlight={[id]} /></>}
      {tab === 'overview' && <TeamStatistics id={id} games={teamGames} client={client} season={season} phase={phase} />}
      {tab === 'players' && <Status loading={playerData.loading} error={playerData.error}>
        <div className="panel-heading team-players-heading"><div><h2>Team players</h2><p>{season} · {phaseLabel(phase)} · appearances available in the dataset</p></div></div>
        <Segmented className="player-switch" value={playerView} onChange={setPlayerView} items={[{value:'general',label:'General'}, {value:'top',label:'Top players'}]} />
        {playerView === 'general'
          ? <TeamRoster rows={(playerData.value ?? []).filter(row => text(row,'Temporada') === season && text(row,'Fase') === phase)} players={players} open={open} />
          : <TeamLeaders rows={(playerData.value ?? []).filter(row => text(row,'Temporada') === season && text(row,'Fase') === phase)} players={players} open={open} />}
      </Status>}
    </section></div></>;
}

function TeamStatistics({ id, games, client, season, phase }: { id: string; games: Row[]; client: AppClient; season: string; phase: string }) {
  const data = useData(`team-stats-${id}`, () => readRows(client, 'teamStats', {column:'Time Id',id}));
  const summary = teamSummary(games, data.value ?? [], id);
  const sections = [
    { title:'Offense', entries:[
      ['Field goals made per game', average(summary.average('Arremessos convertidos'))],
      ['Field goals attempted per game', average(summary.average('Arremessos tentados'))],
      ['Field goals', percentage(summary.ratio('Arremessos convertidos','Arremessos tentados',100))],
      ['Three-pointers made per game', average(summary.average('Bolas de três convertidas'))],
      ['Three-pointers attempted per game', average(summary.average('Bolas de três tentadas'))],
      ['Three-pointers', percentage(summary.ratio('Bolas de três convertidas','Bolas de três tentadas',100))],
      ['Free throws made per game', average(summary.average('Lances livres convertidos'))],
      ['Free throws attempted per game', average(summary.average('Lances livres tentados'))],
      ['Free throws', percentage(summary.ratio('Lances livres convertidos','Lances livres tentados',100))],
    ]},
    { title:'Team stats', entries:[
      ['Rebounds per game', average(summary.average('Rebotes'))],
      ['Assists per game', average(summary.average('Assistências'))],
      ['Steals per game', average(summary.average('Roubos'))],
      ['Blocks per game', average(summary.average('Tocos'))],
      ['Turnovers per game', average(summary.average('Perdas de bola'))],
      ['Assist-to-turnover ratio', average(summary.ratio('Assistências','Perdas de bola'))],
    ]},
  ];
  return <Status loading={data.loading} error={data.error}><div className="team-statistics"><div className="panel-heading"><div><h2>Statistics</h2><p>{season} · {phaseLabel(phase)} · based on available games</p></div></div><h3>Summary</h3><div className="stat-summary-grid"><PlayerMetric label="Points scored / game" value={summary.points} /><PlayerMetric label="Points allowed / game" value={summary.allowed} /><PlayerMetric label="Assists / game" value={summary.average('Assistências')} /><PlayerMetric label="Assist / turnover" value={summary.ratio('Assistências','Perdas de bola')} /></div><p className="coverage-note">Scores: {summary.completedGames} games with complete final scores. Box-score statistics: {summary.statGames} matching {summary.statGames === 1 ? 'game' : 'games'}. Shooting percentages use total makes divided by total attempts.</p><div className="team-stat-columns">{sections.map(section => <section key={section.title}><h3>{section.title}</h3>{section.entries.map(([label,value]) => <div className="team-stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>)}</div></div></Status>;
}

const average = (value: number | null) => value === null ? '—' : value.toLocaleString('en-US', { minimumFractionDigits:1, maximumFractionDigits:1 });
const percentage = (value: number | null) => value === null ? '—' : `${average(value)}%`;

function TeamRoster({ rows, players, open }: { rows: Row[]; players: Row[]; open: Open }) {
  const lines = playerSeasonLines(rows).sort((a,b) => (b.points ?? -1) - (a.points ?? -1));
  if (!lines.length) return <div className="notice">No player appearances available for this season and phase.</div>;
  return <><div className="roster-note">Players inferred from available appearances; this is not necessarily the current roster.</div><div className="table-scroll"><table className="roster-table"><thead><tr><th>PLAYER</th><th>POSITION</th><th>GP</th><th>PTS/G</th><th>REB/G</th><th>AST/G</th><th>FG%</th></tr></thead><tbody>{lines.map(line => {
    const player = players.find(item => text(item,'Jogador Id') === line.playerId);
    const name = player ? text(player,'Jogador') : `Player ${line.playerId}`;
    return <tr key={line.playerId}><td>{player ? <button className="team-link player-link" onClick={() => open({page:'player',id:line.playerId})}><Logo src={text(player,'Foto')} /><span>{name}</span></button> : name}</td><td>{text(player ?? {},'Posição') || '—'}</td><td>{line.games}</td><td>{average(line.points)}</td><td>{average(line.rebounds)}</td><td>{average(line.assists)}</td><td>{percentage(line.fieldGoalPercentage)}</td></tr>;
  })}</tbody></table></div></>;
}

function TeamLeaders({ rows, players, open }: { rows: Row[]; players: Row[]; open: Open }) {
  const lines = playerSeasonLines(rows);
  if (!lines.length) return <div className="notice">No player appearances available for this season and phase.</div>;
  const groups: { title: string; key: 'points' | 'rebounds' | 'assists' | 'fieldGoalPercentage'; suffix: string }[] = [
    { title:'Points per game', key:'points', suffix:'PTS/G' },
    { title:'Rebounds per game', key:'rebounds', suffix:'REB/G' },
    { title:'Assists per game', key:'assists', suffix:'AST/G' },
    { title:'Field goal percentage', key:'fieldGoalPercentage', suffix:'FG%' },
  ];
  return <div className="leader-grid">{groups.map(group => {
    const leaders = lines.filter(line => line[group.key] !== null).sort((a,b) =>
      (b[group.key] ?? -1) - (a[group.key] ?? -1) ||
      text(players.find(player => text(player,'Jogador Id') === a.playerId) ?? {},'Jogador')
        .localeCompare(text(players.find(player => text(player,'Jogador Id') === b.playerId) ?? {},'Jogador'))).slice(0,3);
    return <section className="leader-card" key={group.key}><h3>{group.title}</h3>{leaders.length ? leaders.map((line,index) => {
      const player = players.find(item => text(item,'Jogador Id') === line.playerId);
      return <button className="leader-row" key={line.playerId} onClick={() => player && open({page:'player',id:line.playerId})} disabled={!player}><span className="leader-rank">{index+1}</span><Logo src={text(player ?? {},'Foto')} /><span className="leader-player"><strong>{text(player ?? {},'Jogador') || `Player ${line.playerId}`}</strong><small>{text(player ?? {},'Posição') || 'Position unavailable'} · {line.games} GP</small></span><b>{group.key === 'fieldGoalPercentage' ? percentage(line[group.key]) : average(line[group.key])}<small>{group.suffix}</small></b></button>;
    }) : <p className="leader-empty">Statistic unavailable.</p>}</section>;
  })}</div>;
}

function MiniGame({ label, game, open }: { label: string; game: Row; open: Open }) {
  return <button className="mini-game" onClick={() => open({page:'game', id:text(game,'Jogo Id')})}><small>{label} · {date(gameDate(game))} · {status(game)}</small>{(['visitante','mandante'] as const).map(side => <span className="mini-game-team" key={side}><Logo src={text(game,`Logo ${side}`)} /><span>{text(game,side === 'visitante' ? 'Visitante' : 'Mandante')}</span><strong>{stat(game,`Pontos ${side}`)}</strong></span>)}</button>;
}

function PlayerDetail({ id, players, games, season, phase, client, open }: { id: string; players: Row[]; games: Row[]; season: string; phase: string; client: AppClient; open: Open }) {
  const [tab, setTab] = useState<'games' | 'season'>('games');
  const [shotGame, setShotGame] = useState('');
  const data = useData(`player-${id}`, () => readRows(client,'participation',{ column:'Jogador Id', id }));
  const player = players.find(p => text(p,'Jogador Id') === id);
  if (!player) return <div className="notice error">Player not found.</div>;
  const rows = (data.value ?? []).filter(r => text(r,'Temporada') === season && text(r,'Fase') === phase);
  const line = playerSeasonLines(rows).find(item => item.playerId === id);
  const playerGames = [...rows].sort((a,b) => text(b,'Data do jogo').localeCompare(text(a,'Data do jogo')));
  const latest = playerGames[0];
  const previous = latest && games.find(game => text(game,'Jogo Id') === text(latest,'Jogo Id'));
  const latestTeam = latest ? text(latest,'Time') : '';
  return <Status loading={data.loading} error={data.error}>
    <section className="card player-profile-header"><div className="player-profile-identity"><Logo large src={text(player,'Foto')} /><div><span className="eyebrow">NBA · PLAYER</span><h1>{text(player,'Jogador')}</h1><p>{text(player,'Posição') || 'Position unavailable'}</p>{latestTeam && <button className="player-team-link" onClick={() => open({page:'team',id:text(latest,'Time Id')})}>{previous && <Logo src={text(previous,text(previous,'Mandante Id') === text(latest,'Time Id') ? 'Logo mandante' : 'Logo visitante')} />}{latestTeam}<small>Last team in available {phaseLabel(phase)} data</small></button>}<PlayerBio id={id} /></div></div>{previous && <div className="player-last-game"><h2>Previous game</h2><MiniGame label="NBA" game={previous} open={open} /></div>}</section>
    <div className="workspace-grid player-layout"><div className="left-column"><section className="card player-season-card"><div className="player-season-title"><div><h2>{season || 'Season'} · {phaseLabel(phase)}</h2><p>Per-game averages from available appearances.</p></div></div><PlayerRankGrid client={client} season={season} phase={phase} playerId={id} line={line} /><div className="player-summary-footer">{line?.games ?? 0} {line?.games === 1 ? 'appearance' : 'appearances'} · percentages based on total attempts</div></section></div>
    <section className="card player-content main-panel"><Tabs value={tab} onChange={setTab} items={[{value:'games',label:'Games'}, {value:'season',label:'Season'}]} />
      {tab === 'games' && <><div className="panel-heading"><div><h2>NBA · {season}</h2><p>Game-by-game performance · {phaseLabel(phase)}</p></div></div>{!playerGames.length ? <div className="notice">No appearances in this selection.</div> : <div className="table-scroll"><table className="player-games-table"><thead><tr><th>DATE</th><th>OPPONENT</th><th>RESULT</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>TOV</th><th>FG</th><th>3PT</th><th>FT</th><th>+/-</th><th>SHOTS</th></tr></thead><tbody>{playerGames.map((row,index) => {
        const game = games.find(item => text(item,'Jogo Id') === text(row,'Jogo Id'));
        const teamId = text(row,'Time Id');
        const home = game ? text(game,'Mandante Id') === teamId : false;
        const opponent = game ? text(game, home ? 'Visitante' : 'Mandante') : 'Opponent unavailable';
        const teamScore = game ? number(game, home ? 'Pontos mandante' : 'Pontos visitante') : null;
        const opponentScore = game ? number(game, home ? 'Pontos visitante' : 'Pontos mandante') : null;
        const final = game && text(game,'Situação') === 'FINAL' && teamScore !== null && opponentScore !== null && teamScore !== opponentScore;
        const won = final && teamScore > opponentScore;
        const result = final ? won ? 'W' : 'L' : game ? status(game) : '—';
        return <tr key={`${text(row,'Jogo Id')}-${index}`}><td>{date(text(row,'Data do jogo'))}</td><td>{game ? <button className="inline-link" onClick={() => open({page:'game',id:text(row,'Jogo Id')})}>{home ? 'vs' : '@'} {opponent}</button> : opponent}</td><td><span className={won ? 'game-result won' : final ? 'game-result lost' : 'game-result'}>{result}{final ? ` ${teamScore}–${opponentScore}` : ''}</span></td><td>{stat(row,'Minutos brutos')}</td><td>{stat(row,'Pontos brutos')}</td><td>{stat(row,'Rebotes brutos')}</td><td>{stat(row,'Assistências brutas')}</td><td>{stat(row,'Roubos')}</td><td>{stat(row,'Tocos')}</td><td>{stat(row,'Perdas de bola')}</td><td>{stat(row,'Arremessos convertidos')}/{stat(row,'Arremessos tentados')}</td><td>{stat(row,'Bolas de três convertidas')}/{stat(row,'Bolas de três tentadas')}</td><td>{stat(row,'Lances livres convertidos')}/{stat(row,'Lances livres tentados')}</td><td>{stat(row,'Mais menos')}</td><td><button className="inline-link" onClick={() => { setShotGame(text(row,'Jogo Id')); setTab('season'); }}>Shot map</button></td></tr>;
      })}</tbody></table></div>}</>}
      {tab === 'season' && <><div className="shotmap-panel"><div className="shotmap-heading"><h2>Game shot map</h2><p>Field-goal attempts · select a game</p></div>{playerGames.length ? <><label className="shotmap-select">Game <select value={playerGames.some(row => text(row,'Jogo Id') === shotGame) ? shotGame : text(playerGames[0],'Jogo Id')} onChange={event => setShotGame(event.target.value)}>{playerGames.map(row => {
        const game = games.find(item => text(item,'Jogo Id') === text(row,'Jogo Id'));
        const home = game && text(game,'Mandante Id') === text(row,'Time Id');
        return <option key={text(row,'Jogo Id')} value={text(row,'Jogo Id')}>{date(text(row,'Data do jogo'))} · {game ? `${home ? 'vs' : '@'} ${text(game,home ? 'Visitante' : 'Mandante')}` : text(row,'Time')}</option>;
      })}</select></label>{(() => {
        const selected = playerGames.find(row => text(row,'Jogo Id') === shotGame) ?? playerGames[0];
        const gameId = text(selected,'Jogo Id');
        return <GameShotmap key={`${id}-${gameId}`} gameId={gameId} playerId={id} expectedMade={number(selected,'Arremessos convertidos')} expectedAttempts={number(selected,'Arremessos tentados')} />;
      })()}</> : <div className="notice">No games available for a shot map.</div>}</div><div className="player-season-details"><h3>Season statistics</h3><div className="team-stat-columns"><section>{[['Appearances',String(line?.games ?? 0)],['Minutes per game',average(line?.minutes ?? null)],['Points per game',average(line?.points ?? null)],['Rebounds per game',average(line?.rebounds ?? null)],['Assists per game',average(line?.assists ?? null)]].map(([label,value]) => <div className="team-stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section><section>{[['Field goals (total)',`${line?.fieldGoalsMade ?? '—'}/${line?.fieldGoalsAttempted ?? '—'}`],['Three-pointers (total)',`${line?.threePointersMade ?? '—'}/${line?.threePointersAttempted ?? '—'}`],['Free throws (total)',`${line?.freeThrowsMade ?? '—'}/${line?.freeThrowsAttempted ?? '—'}`],['Field goal percentage',percentage(line?.fieldGoalPercentage ?? null)],['Three-point percentage',percentage(line?.threePointPercentage ?? null)]].map(([label,value]) => <div className="team-stat-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section></div></div></>}
    </section></div>
  </Status>;
}

function PlayerBio({id}: {id: string}) {
  const data = useData(`player-bio-${id}`, () => fetchPlayerProfile(id));
  if (data.loading) return <p className="player-bio">Loading profile...</p>;
  if (data.error || !data.value) return <p className="player-bio">Profile details unavailable{data.error ? `: ${data.error}` : '.'}</p>;
  const bio = data.value;
  const details = [bio.country ? `Born in ${bio.country}` : '', bio.birthDate ? `${date(bio.birthDate)}${bio.age !== null ? ` (age ${bio.age})` : ''}` : '', bio.height, bio.weight, bio.jersey ? `Current jersey #${bio.jersey}` : ''].filter(Boolean);
  return <p className="player-bio">{details.length ? details.join(' · ') : 'Profile details unavailable.'}</p>;
}

const rankMetrics: {label: string; key: RankMetric; percent?: boolean}[] = [
  {label:'PTS',key:'points'}, {label:'REB',key:'rebounds'}, {label:'AST',key:'assists'}, {label:'STL',key:'steals'}, {label:'BLK',key:'blocks'},
  {label:'MIN',key:'minutes'}, {label:'FG%',key:'fieldGoalPercentage',percent:true}, {label:'3P%',key:'threePointPercentage',percent:true}, {label:'TOV',key:'turnovers'}, {label:'+/-',key:'plusMinus'},
];

function PlayerRankGrid({client, season, phase, playerId, line}: {client: AppClient; season: string; phase: string; playerId: string; line?: PlayerSeasonLine}) {
  const data = useData(`league-ranks-${season}-${phase}`, () => readLeagueRows(client,season,phase));
  const lines = playerSeasonLines(data.value ?? []);
  return <><div className="player-stat-grid">{rankMetrics.map(item => {
    const rank = playerRank(lines,playerId,item.key);
    const values = lines.map(player => player[item.key]).filter((value): value is number => value !== null);
    const ratio = rank && rank.total >= 5 && Math.min(...values) < Math.max(...values) ? (rank.rank - 1) / (rank.total - 1) : null;
    const color = item.key === 'turnovers' || ratio === null ? '' : ratio < 1/3 ? 'rank-high' : ratio < 2/3 ? 'rank-mid' : 'rank-low';
    const value = line?.[item.key] ?? null;
    return <div className={`metric rank-metric ${color}`} key={item.key}><span>{item.label}</span><strong>{item.percent ? percentage(value) : average(value)}</strong><small>{rank ? `#${rank.rank}` : '—'}</small></div>;
  })}</div><p className="rank-note">{data.loading ? 'Loading rankings...' : data.error ? `Rankings unavailable: ${data.error}` : 'Color shows relative rank among available players, without minimum-game qualification. Higher TOV is ranked higher but not color-coded.'}</p></>;
}

function PlayerMetric({ label, value, isPercentage = false }: { label: string; value: number | null | undefined; isPercentage?: boolean }) {
  return <div className="metric"><span>{label}</span><strong>{isPercentage ? percentage(value ?? null) : average(value ?? null)}</strong></div>;
}

function GameShotmap({ gameId, playerId, expectedMade, expectedAttempts }: { gameId: string; playerId: string; expectedMade: number | null; expectedAttempts: number | null }) {
  const [period, setPeriod] = useState(0);
  const data = useData(`shots-${gameId}-${playerId}`, () => fetchShots(gameId, playerId));
  if (data.loading) return <div className="notice" role="status">Loading shot locations from ESPN...</div>;
  if (data.error || !data.value) return <div className="notice error" role="alert">Shot locations unavailable: {data.error ?? 'No data returned.'}</div>;
  const { shots, attempts, made, unplotted } = data.value;
  const shown = shots.filter(shot => !period || shot.period === period);
  const shownMade = shown.filter(shot => shot.made).length;
  const periods = [1, 2, 3, 4, ...[...new Set(shots.map(shot => shot.period).filter(value => value > 4))].sort((a,b) => a-b)];
  const mismatch = (expectedAttempts !== null && attempts !== expectedAttempts) || (expectedMade !== null && made !== expectedMade);
  return <><div className="filter-pills shotmap-periods" aria-label="Shot map period filter">{[0, ...periods].map(value => <button key={value} aria-pressed={period === value} className={period === value ? 'selected' : ''} onClick={() => setPeriod(value)}>{value === 0 ? 'All' : value <= 4 ? `Q${value}` : `OT${value - 4}`}</button>)}</div>
    <div className="shotmap-summary"><strong>{shownMade}/{shown.length}</strong><span>mapped field goals made / attempted{shown.length ? ` · ${(100 * shownMade / shown.length).toFixed(1)}%` : ''}</span></div>
    <div className="shotmap-court"><svg viewBox="0 0 500 470" role="img" aria-label={`${shownMade} made and ${shown.length - shownMade} missed mapped field goals${period ? ` in ${period <= 4 ? `quarter ${period}` : `overtime ${period - 4}`}` : ''}.`}>
      <g className="court-lines"><rect x="1" y="1" width="498" height="468" /><path d="M170 1v189h160V1M170 190a80 80 0 0 0 160 0M210 1v51.5a40 40 0 0 0 80 0V1M220 190a30 30 0 0 0 60 0M220 40h60M250 40v5M30 1v141.5a237.5 237.5 0 0 0 440 0V1M190 470a60 60 0 0 1 120 0" /><circle cx="250" cy="52.5" r="7.5" /></g>
      {shown.map(shot => <g key={shot.id} className={shot.made ? 'shot-made' : 'shot-missed'} transform={`translate(${shot.x * 10} ${shot.y * 10 + 42.5})`}><title>{shot.description}</title>{shot.made ? <circle r="7" /> : <path d="M-5 -5L5 5M5 -5L-5 5" />}</g>)}
    </svg></div><div className="shotmap-legend"><span><b className="legend-made">●</b> Made</span><span><b className="legend-missed">×</b> Missed</span></div>
    <p className="shotmap-footnote">Source: ESPN play-by-play. Free throws are excluded; positions are approximate. {unplotted > 0 && `${unplotted} recorded ${unplotted === 1 ? 'attempt has' : 'attempts have'} missing or out-of-court coordinates or other required details. `}{mismatch && `Play-by-play records ${made}/${attempts} FG; the available box score shows ${expectedMade ?? '—'}/${expectedAttempts ?? '—'}. Data may be incomplete or revised.`}{!attempts && ' No field-goal attempts were found in the play-by-play.'}</p>
  </>;
}
