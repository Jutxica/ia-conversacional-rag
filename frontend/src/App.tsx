import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import { MessageSquare, Plus, User, Bot, Send, ShieldCheck, Settings, ExternalLink, FileText, Loader2, LogOut } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { supabase } from './supabaseClient';

// --- Types ---
interface Citation {
  id: string;
  title: string;
  url: string;
  snippet?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  metadata?: {
    confidence: { level: string; percentage: number; avg_score: number };
    comparative_mode: boolean;
  };
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

// --- Components ---
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    
    if (error) {
      setError('Credenciais inválidas. Verifique seu e-mail e senha.');
    }
    setLoading(false);
  };

  return (
    <div className="login-overlay">
      <div className="login-card">
        <img src="/Login svg.svg" className="login-logo" alt="Dehon AI" />
        <h2>Biblioteca Dehoniana</h2>
        <p>Acesso restrito a pesquisadores autorizados.</p>
        
        <form className="login-form" onSubmit={handleLogin}>
          <div className="input-group">
            <label>E-mail</label>
            <input 
              type="email" 
              className="login-input" 
              placeholder="seu@email.com" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="input-group">
            <label>Senha de Acesso</label>
            <input 
              type="password" 
              className="login-input" 
              placeholder="••••••••" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <div className="error-text" style={{ color: '#eb144c', fontSize: '0.8rem', marginBottom: '1rem' }}>{error}</div>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : <ShieldCheck size={18} />}
            {loading ? 'Autenticando...' : 'Acessar Biblioteca'}
          </button>
        </form>

        <div className="login-footer">
          Não tem uma conta? <a href="mailto:admin@dehon.it">Solicitar Registro</a>
        </div>
      </div>
    </div>
  );
};

// --- Main App Component ---
export default function App() {
  const [session, setSession] = useState<any>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  const currentChat = conversations.find(c => c.id === currentId);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentChat?.messages, isStreaming]);

  const startNewChat = () => {
    const newChat: Conversation = {
      id: Date.now().toString(),
      title: 'Nova Pesquisa',
      messages: []
    };
    setConversations([newChat, ...conversations]);
    setCurrentId(newChat.id);
  };

  const handleSend = async () => {
    if (!input.trim() || !currentId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setConversations(prev => prev.map(c => 
      c.id === currentId 
        ? { ...c, messages: [...c.messages, userMessage], title: c.messages.length === 0 ? input.slice(0, 30) : c.title }
        : c
    ));

    setInput('');
    setIsStreaming(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      let assistantMessageId = (Date.now() + 1).toString();

      setConversations(prev => prev.map(c => 
        c.id === currentId 
          ? { ...c, messages: [...c.messages, { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date() }] }
          : c
      ));

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'token') {
              setConversations(prev => prev.map(c => 
                c.id === currentId 
                  ? { 
                      ...c, 
                      messages: c.messages.map(m => 
                        m.id === assistantMessageId ? { ...m, content: m.content + data.content } : m
                      ) 
                    }
                  : c
              ));
            } else if (data.type === 'citations') {
              setConversations(prev => prev.map(c => 
                c.id === currentId 
                  ? { 
                      ...c, 
                      messages: c.messages.map(m => 
                        m.id === assistantMessageId ? { ...m, citations: data.content } : m
                      ) 
                    }
                  : c
              ));
            } else if (data.type === 'metadata') {
              setConversations(prev => prev.map(c => 
                c.id === currentId 
                  ? { 
                      ...c, 
                      messages: c.messages.map(m => 
                        m.id === assistantMessageId ? { ...m, metadata: data.content } : m
                      ) 
                    }
                  : c
              ));
            } else if (data.type === 'done') {
              setIsStreaming(false);
            }
          }
        }
      }
    } catch (err) {
      console.error('Erro ao conectar com o backend:', err);
      setError('Falha na conexão com o servidor Dehon AI.');
      setIsStreaming(false);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  if (!session) {
    return <LoginPage />;
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <header className="sidebar-header">
          <div className="brand">
            <img src="/Sidebar svg.svg" className="logo-small" alt="Dehon AI" />
            <span>Dehon AI</span>
          </div>
        </header>

        <button className="new-chat-btn" onClick={startNewChat}>
          <Plus size={16} /> Nova Pesquisa
        </button>

        <div className="history-list">
          <div className="section-label">Recentes</div>
          {conversations.map(c => (
            <div 
              key={c.id} 
              className={`history-item ${c.id === currentId ? 'active' : ''}`}
              onClick={() => setCurrentId(c.id)}
            >
              <span className="history-title">{c.title}</span>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-profile" onClick={handleLogout} title="Clique para sair">
            <div className="avatar">{session.user.email[0].toUpperCase()}</div>
            <span className="username">{session.user.email.split('@')[0]}</span>
            <LogOut size={14} className="settings-icon" />
          </div>
        </div>
      </aside>

      <main className="main-content">
        {!currentId ? (
          <div className="hero-section">
            <img src="/Navbar svg.svg" className="hero-logo" alt="Dehon AI Logo" />
            <h1>Qual obra vamos analisar hoje?</h1>
            <div className="quick-suggestions">
               <div className="suggestion-card" onClick={startNewChat}>O Catecismo Social</div>
               <div className="suggestion-card" onClick={startNewChat}>Teologia da Reparação</div>
               <div className="suggestion-card" onClick={startNewChat}>Cartas aos Escolásticos</div>
            </div>
          </div>
        ) : (
          <div className="chat-layout">
            <header className="top-bar">
               <div className="model-info">
                 <img src="/Navbar svg.svg" className="logo-tiny" alt="Navbar Logo" />
                 <span className="model-label">Dehon AI</span>
                 <span className="model-version">v1.2 Supabase</span>
               </div>
               <div className="sync-status">
                 <ShieldCheck size={14} className="status-icon active" />
                 <span>Pesquisa em Tempo Real</span>
               </div>
            </header>

            <div className="chat-container" ref={scrollRef}>
              {currentChat?.messages.map((m, idx) => (
                <div key={m.id} className={`message-row ${m.role} animate-slide-up`}>
                  <div className="message-container">
                    <div className="message-icon-wrapper">
                      {m.role === 'user' ? (
                        <div className="user-avatar">{session.user.email[0].toUpperCase()}</div>
                      ) : (
                        <div className="bot-avatar">
                          <img src="/Avatar svg.svg" alt="Bot" className="bot-img" />
                        </div>
                      )}
                    </div>
                    <div className="message-body">
                      {m.role === 'user' ? (
                        <div className="user-header">
                          <span className="user-name">Sua Pesquisa</span>
                        </div>
                      ) : (
                        <div className="assistant-header">
                          <span className="assistant-name">Dehon AI</span>
                          <span className="assistant-status">Magistério Dehoniano</span>
                          {m.metadata && (
                            <span className={`badge confidence-${m.metadata.confidence.level.toLowerCase()}`}>
                               Confiança {m.metadata.confidence.level} ({m.metadata.confidence.percentage}%)
                            </span>
                          )}
                        </div>
                      )}
                      {m.role === 'assistant' && m.content === '' && isStreaming && idx === currentChat.messages.length - 1 ? (
                        <div className="thinking-container fade-in">
                          <div className="thinking-trace"></div>
                          <div className="thinking-text">Consultando Magistério Dehoniano...</div>
                        </div>
                      ) : (
                        <div className={m.role === 'assistant' ? 'gradual-reveal' : ''}>
                          <ReactMarkdown>{m.content}</ReactMarkdown>
                        </div>
                      )}
                      {isStreaming && m.content !== '' && idx === currentChat.messages.length - 1 && <span className="typing-cursor"></span>}
                    </div>
                    {m.role === 'assistant' && m.citations && m.citations.length > 0 && (() => {
                        const regex = new RegExp('\\[(\\d+)\\]', 'g');
                        const referencedIndices = [...m.content.matchAll(regex)].map(match => parseInt(match[1]) - 1);
                        const filteredCitations = m.citations.filter((_, idx) => referencedIndices.includes(idx));
                        if (filteredCitations.length === 0) return null;

                        return (
                          <div className="citations-section">
                            <div className="section-divider"></div>
                            <div className="sources-header">Evidências Documentais:</div>
                            <div className="sources-list">
                              {filteredCitations.map((cite, cIdx) => (
                                <div key={cIdx} className={`source-item stagger-${Math.min(cIdx + 1, 5)}`}>
                                  <div className="source-reference">
                                    <a href={cite.url} target="_blank" rel="noopener noreferrer" className="source-link">
                                      <span className="ref-label">[{referencedIndices.find(i => m.citations[i].id === cite.id) + 1}]</span>
                                      {cite.title} <ExternalLink size={12} style={{ display: 'inline', marginLeft: '4px' }} />
                                    </a>
                                  </div>
                                  <div className="source-snippet">
                                    {cite.snippet && (cite.snippet.length > 300 ? cite.snippet.substring(0, 300) + "..." : cite.snippet)}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })()}
                  </div>
                </div>
              ))}
            </div>

            <div className="input-panel">
              <div className="input-container">
                <textarea 
                  placeholder="Explorar obras do Padre Dehon..." 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                  rows={1}
                  disabled={isStreaming}
                />
                <button 
                  className={`send-button ${input.trim() ? 'enabled' : ''}`}
                  onClick={handleSend}
                  disabled={!input.trim() || isStreaming}
                >
                  <Send size={18} />
                </button>
              </div>
              <div className="footer-note">Ambiente Seguro de Pesquisa | Sacerdotes do Sagrado Coração de Jesus</div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
