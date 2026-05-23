import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import AdminApp from './AdminApp.tsx'
import AdminLoginPage from './admin/AdminLoginPage.tsx'
import { supabase } from './supabaseClient'
import ErrorBoundary from './components/ui/ErrorBoundary'

// Authorized domains/emails for Admin access
const AUTHORIZED_ADMINS = ['fr.utxicascj@gmail.com']; // Specific emails
const AUTHORIZED_DOMAINS = ['dehon.ai', 'congregacao.org']; // Domains

function AppRoot() {
  const [view, setView] = useState<'chat' | 'admin' | 'secret-admin'>('chat');
  const [session, setSession] = useState<any>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Check initial path
    if (window.location.pathname === '/admin') {
      setView('admin');
    } else if (window.location.pathname === '/secret-admin') {
      setView('secret-admin');
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      checkAdmin(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      checkAdmin(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  const checkAdmin = (session: any) => {
    if (!session?.user?.email) {
      setIsAdmin(false);
      return;
    }
    const email = session.user.email.toLowerCase();
    const domain = email.split('@')[1];
    
    const isAuth = AUTHORIZED_ADMINS.includes(email) || AUTHORIZED_DOMAINS.includes(domain);
    setIsAdmin(isAuth);
  };

  const handleSwitchView = (newView: 'chat' | 'admin') => {
    setView(newView);
    window.history.pushState({}, '', newView === 'admin' ? '/admin' : '/');
  };

  if (view === 'secret-admin') {
    return (
      <AdminLoginPage
        onLoginSuccess={() => {
          setView('admin');
          window.history.pushState({}, '', '/admin');
        }}
        onBackToChat={() => handleSwitchView('chat')}
      />
    );
  }

  if (view === 'admin') {
    return <AdminApp onBackToChat={() => handleSwitchView('chat')} />;
  }

  return <App isAdmin={isAdmin} onSwitchToAdmin={() => handleSwitchView('admin')} />;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <AppRoot />
    </ErrorBoundary>
  </StrictMode>,
)
