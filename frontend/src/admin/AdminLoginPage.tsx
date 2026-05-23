import React, { useState } from 'react';
import { ShieldCheck, Loader2, User, Lock, ArrowRight, HelpCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/chat', '') || 'http://localhost:8000';

interface Props {
  onLoginSuccess: () => void;
  onBackToChat: () => void;
}

export default function AdminLoginPage({ onLoginSuccess, onBackToChat }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao realizar login administrativo.');
      }

      localStorage.setItem('dehon_admin_token', data.token);
      onLoginSuccess();
    } catch (err: any) {
      setError(err.message || 'Credenciais inválidas.');
    } finally {
      setLoading(false);
    }
  };

  const handleAutofill = () => {
    setUsername('admin');
    // Pre-fill the admin hash password from backend config
    setPassword('8f603f5ccadffbf6e9ac94273153fa72');
  };

  return (
    <div className="adm-root" style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0d1117' }}>
      <div className="adm-modal-overlay" style={{ position: 'relative', background: 'transparent' }}>
        <div className="adm-modal-content" style={{ maxWidth: '400px', padding: '24px', background: '#161b22', border: '1px solid #30363d', borderRadius: '12px' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', marginBottom: '24px', textAlign: 'center' }}>
            <div style={{ background: 'rgba(201, 169, 110, 0.15)', color: '#c9a96e', padding: '12px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={32} />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#f0f6fc', margin: 0 }}>Portal Admin Direto</h2>
              <p style={{ fontSize: '12px', color: '#8b949e', marginTop: '4px', margin: 0 }}>Autenticação local sem restrições do provedor de e-mail.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="adm-meta-field" style={{ marginBottom: 0 }}>
              <label style={{ fontSize: '12px', color: '#8b949e', marginBottom: '6px', display: 'block' }}>Usuário</label>
              <div style={{ position: 'relative' }}>
                <User size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b949e' }} />
                <input
                  type="text"
                  required
                  placeholder="admin"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="adm-input"
                  style={{ paddingLeft: '36px', width: '100%' }}
                />
              </div>
            </div>

            <div className="adm-meta-field" style={{ marginBottom: 0 }}>
              <label style={{ fontSize: '12px', color: '#8b949e', marginBottom: '6px', display: 'block' }}>Senha de Segurança</label>
              <div style={{ position: 'relative' }}>
                <Lock size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b949e' }} />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••••••••••••••••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="adm-input"
                  style={{ paddingLeft: '36px', width: '100%' }}
                />
              </div>
            </div>

            {error && (
              <div className="adm-feedback adm-feedback--error" style={{ margin: 0, padding: '10px 12px' }}>
                <span style={{ fontSize: '12px' }}>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="adm-cta-btn"
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px 16px', fontSize: '14px' }}
            >
              {loading ? <Loader2 size={16} className="spinning" /> : <>Entrar no Painel <ArrowRight size={16} /></>}
            </button>
          </form>

          <div style={{ marginTop: '20px', borderTop: '1px solid #21262d', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              onClick={handleAutofill}
              className="adm-refresh-btn"
              style={{ width: '100%', border: '1px dashed #c9a96e', color: '#c9a96e', padding: '8px', borderRadius: '6px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', cursor: 'pointer' }}
            >
              <HelpCircle size={14} /> Preencher Credenciais de Teste
            </button>

            <button
              onClick={onBackToChat}
              style={{ background: 'transparent', border: 'none', color: '#8b949e', fontSize: '12px', cursor: 'pointer', textAlign: 'center', textDecoration: 'underline' }}
            >
              Voltar ao Chat de Pesquisa
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
