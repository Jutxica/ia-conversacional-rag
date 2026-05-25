import React, { useState, useEffect } from 'react';
import './index.css';
import './admin/admin.css';
import { supabase } from './supabaseClient';
import AdminDashboardPage from './admin/AdminDashboardPage';
import LoginPage from './components/layout/LoginPage';

interface AdminAppProps {
  onBackToChat: () => void;
}

export default function AdminApp({ onBackToChat }: AdminAppProps) {
  const [session, setSession] = useState<any>(null);
  const [localToken, setLocalToken] = useState<string | null>(null);
  const [isAppLoading, setIsAppLoading] = useState(true);

  useEffect(() => {
    // Check for local admin token first
    const token = localStorage.getItem('dehon_admin_token');
    if (token) {
      setLocalToken(token);
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    const timer = setTimeout(() => setIsAppLoading(false), 1000);
    return () => {
      subscription.unsubscribe();
      clearTimeout(timer);
    };
  }, []);

  if (isAppLoading) {
    return (
      <div className="splash-screen">
        <div className="splash-content">
          <img src="/Navbar.png" className="splash-logo" alt="Dehon AI Admin" />
          <div className="splash-loader"><div className="loader-bar"></div></div>
          <p className="splash-text">Gestão do Corpus - Carregando...</p>
        </div>
      </div>
    );
  }

  // If local token exists, bypass Supabase auth
  if (localToken) {
    const handleLocalLogout = () => {
      localStorage.removeItem('dehon_admin_token');
      window.location.reload();
    };

    return (
      <div className="admin-app-container">
        <AdminDashboardPage 
          token={localToken} 
          onLogout={handleLocalLogout}
          onBackToChat={onBackToChat}
        />
      </div>
    );
  }

  if (!session) {
    return <LoginPage onLoginSuccess={() => window.location.reload()} />;
  }

  const userEmail = session.user?.email || '';
  const isAdmin = userEmail === 'fr.utxicascj@gmail.com' ||
                  userEmail === 'jutxica2202@gmail.com' ||
                  userEmail.endsWith('@dehon.ai') ||
                  userEmail.endsWith('@congregacao.org');

  if (!isAdmin) {
    return (
      <div className="admin-login-root">
        <div className="admin-login-card">
          <div className="admin-login-header">
            <h1 className="admin-login-title">Acesso Negado</h1>
            <p className="admin-login-subtitle" style={{ color: '#ff6b6b' }}>
              O email {userEmail} não possui privilégios administrativos.
            </p>
          </div>
          <button 
            onClick={() => supabase.auth.signOut().then(() => window.location.reload())}
            className="admin-login-btn"
          >
            Sair e Fazer Login com Outra Conta
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-app-container">
      <AdminDashboardPage 
        token={session.access_token} 
        onLogout={() => supabase.auth.signOut().then(() => window.location.reload())}
        onBackToChat={onBackToChat}
      />
    </div>
  );
}
