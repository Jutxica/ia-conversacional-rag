import React, { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/chat', '') || 'http://localhost:8000';

interface Props {
  onLogin: (token: string) => void;
}

export default function AdminLoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Credenciais inválidas. Tente novamente.');
        return;
      }

      onLogin(data.token);
    } catch (err) {
      setError('Erro de conexão com o servidor. Verifique se o backend está rodando.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-root">
      <div className="admin-login-card">
        {/* Logo / Branding */}
        <div className="admin-login-header">
          <div className="admin-login-logo">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="20" fill="url(#grad)" />
              <text x="50%" y="54%" dominantBaseline="middle" textAnchor="middle" fontSize="18" fill="white" fontFamily="serif" fontWeight="bold">D</text>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#c9a96e" />
                  <stop offset="1" stopColor="#8b6c42" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="admin-login-title">Dehon AI</h1>
          <p className="admin-login-subtitle">Portal Administrativo</p>
        </div>

        {/* Form */}
        <form className="admin-login-form" onSubmit={handleSubmit}>
          <div className="admin-login-field">
            <label htmlFor="admin-username">Usuário</label>
            <input
              id="admin-username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="admin"
              autoComplete="username"
              required
              autoFocus
            />
          </div>

          <div className="admin-login-field">
            <label htmlFor="admin-password">Senha</label>
            <input
              id="admin-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          {error && (
            <div className="admin-login-error">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7.5" stroke="#ff6b6b"/><path d="M8 4.5v4M8 10.5v1" stroke="#ff6b6b" strokeLinecap="round"/></svg>
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            className="admin-login-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="admin-spinner" />
                Autenticando...
              </>
            ) : (
              'Entrar no Portal'
            )}
          </button>
        </form>

        <p className="admin-login-footer">
          Acesso restrito a administradores autorizados
        </p>
      </div>
    </div>
  );
}
