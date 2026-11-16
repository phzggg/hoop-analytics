import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ensureSignedInWithFabric, initEmbeddedAuth } from '@microsoft/rayfin-auth-provider-fabric';
import { ArrowRight } from 'lucide-react';
import { createClient } from './client';
import { Dashboard, Brand } from './dashboard';
import { loadPublicSnapshot } from './snapshot';
import { loadPublishedSnapshot } from './public-data';
import './style.css';

type Setup = Awaited<ReturnType<typeof createClient>>;
const errorMessage = (error: unknown) => error instanceof Error ? error.message : String(error);

function AuthenticatedApp() {
  const [setup, setSetup] = useState<Setup>();
  const [authenticated, setAuthenticated] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [authError, setAuthError] = useState('');
  useEffect(() => {
    let active = true;
    createClient().then(async configured => {
      const session = await initEmbeddedAuth(configured.client.auth, configured.options);
      if (!session && configured.client.auth.getSession().isAnonymous) await configured.client.auth.signOut();
      if (!active) return;
      setSetup(configured);
      const current = session ?? configured.client.auth.getSession();
      setAuthenticated(current.isAuthenticated && !current.isAnonymous);
    }).catch(error => { if (active) setAuthError(errorMessage(error)); })
      .finally(() => { if (active) setInitializing(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!setup || !authenticated) return;
    return setup.client.auth.onSessionChange(session => {
      if (!session?.isAuthenticated || session.isAnonymous) setAuthenticated(false);
    });
  }, [setup, authenticated]);
  async function signIn() {
    if (!setup) return;
    try {
      const session = await ensureSignedInWithFabric(setup.client.auth, setup.options);
      setAuthenticated(session.isAuthenticated && !session.isAnonymous);
      setAuthError('');
    } catch (error) { setAuthError(errorMessage(error)); }
  }
  if (initializing) return <div className="gate"><div className="notice">Preparing Fabric access...</div></div>;
  if (!authenticated || !setup) return <div className="gate"><div className="gate-card"><Brand /><h1>Your view of the NBA.</h1><p>Sign in with your Fabric account to explore games, teams and players.</p>{authError && <p className="error">{authError}</p>}{setup && <button className="primary" onClick={signIn}>Sign in with Fabric <ArrowRight size={16} /></button>}</div></div>;
  return <Dashboard client={setup.client} />;
}

function PublicApp({ url, published }: { url: string; published?: false } | { url?: never; published: true }) {
  const [snapshot, setSnapshot] = useState<Awaited<ReturnType<typeof loadPublicSnapshot>>>();
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    const request = published ? loadPublishedSnapshot() : loadPublicSnapshot(url);
    request.then(value => { if (active) setSnapshot(value); })
      .catch(reason => { if (active) setError(errorMessage(reason)); });
    return () => { active = false; };
  }, [url, published]);
  if (error) return <div className="gate"><div className="notice error" role="alert">Unable to load public NBA data: {error}</div></div>;
  if (!snapshot) return <div className="gate"><div className="notice">Loading public NBA data...</div></div>;
  return <Dashboard client={{ snapshot, scheduled: published }} />;
}

function App() {
  const publicUrl = import.meta.env.VITE_PUBLIC_SNAPSHOT_URL;
  if (import.meta.env.VITE_PUBLIC_DATA === 'true') return <PublicApp published />;
  return publicUrl ? <PublicApp url={publicUrl} /> : <AuthenticatedApp />;
}

createRoot(document.getElementById('root')!).render(<App />);
