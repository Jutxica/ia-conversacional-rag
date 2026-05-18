import React, { useState, useEffect } from 'react';
import './index.css';
import { supabase } from './supabaseClient';
import AdminDashboard from './components/admin/AdminDashboard';
import LoginPage from './components/layout/LoginPage';

export default function AdminApp() {
  const [session, setSession] = useState<any>(null);
  const [isAppLoading, setIsAppLoading] = useState(true);

  useEffect(() => {
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

  if (!session) {
    return <LoginPage onLoginSuccess={() => window.location.reload()} />;
  }

  return (
    <div className="admin-app-container">
      <AdminDashboard onClose={() => {
        // In a standalone app, maybe we just redirect or show a "Go to Chat" button
        window.location.href = '/';
      }} />
    </div>
  );
}
