import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import { MessageSquare, Plus, User, Bot, Send, ShieldCheck, Settings, ExternalLink, FileText, Loader2, LogOut, SquarePen, Search } from 'lucide-react';
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
  isGreeting?: boolean;
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
  const [scope, setScope] = useState('Geral');
  const [isScopeOpen, setIsScopeOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
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
    const hour = new Date().getHours();
    let greeting = 'Boa noite';
    if (hour >= 5 && hour < 12) greeting = 'Bom dia';
    else if (hour >= 12 && hour < 18) greeting = 'Boa tarde';

    const userName = session?.user?.email?.split('@')[0] || 'Pesquisador';
    const formattedName = userName.charAt(0).toUpperCase() + userName.slice(1);

    const initialMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `### ${greeting}, ${formattedName}.\nComo posso guiar sua pesquisa hoje?`,
      timestamp: new Date(),
      isGreeting: true
    };

    const newChat: Conversation = {
      id: Date.now().toString() + '_chat',
      title: 'Nova Pesquisa',
      messages: [initialMessage]
    };
    setConversations([newChat, ...conversations]);
    setCurrentId(newChat.id);
  };

  const executeChatLogic = async (chatId: string, query: string, currentHistory: Message[]) => {
    setIsStreaming(true);
    setError(null);
    setInput('');

    try {
      const historyPayload = currentHistory.map(m => ({ role: m.role, content: m.content }));
      
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/chat';
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, scope: scope, history: historyPayload }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      let assistantMessageId = (Date.now() + 1).toString();

      setConversations(prev => prev.map(c => 
        c.id === chatId 
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
                c.id === chatId 
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
                c.id === chatId 
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
                c.id === chatId 
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

  const startNewChatWithInput = (query: string) => {
    if (!query.trim()) return;

    const hour = new Date().getHours();
    let greeting = 'Boa noite';
    if (hour >= 5 && hour < 12) greeting = 'Bom dia';
    else if (hour >= 12 && hour < 18) greeting = 'Boa tarde';

    const userName = session?.user?.email?.split('@')[0] || 'Pesquisador';
    const formattedName = userName.charAt(0).toUpperCase() + userName.slice(1);

    const initialMessage: Message = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `### ${greeting}, ${formattedName}.\nComo posso guiar sua pesquisa hoje?`,
      timestamp: new Date(),
      isGreeting: true
    };

    const userMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    const newChatId = Date.now().toString() + '_chat';
    const newChat: Conversation = {
      id: newChatId,
      title: query.slice(0, 30),
      messages: [initialMessage, userMessage]
    };
    
    setConversations([newChat, ...conversations]);
    setCurrentId(newChatId);
    
    executeChatLogic(newChatId, query, [initialMessage]);
  };

  const handleSend = () => {
    if (!input.trim() || !currentId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    const targetChat = conversations.find(c => c.id === currentId);
    if (!targetChat) return;

    setConversations(prev => prev.map(c => 
      c.id === currentId 
        ? { ...c, messages: [...c.messages, userMessage], title: c.messages.length === 0 ? input.slice(0, 30) : c.title }
        : c
    ));

    const query = input;
    const currentHistory = targetChat.messages;
    executeChatLogic(currentId, query, currentHistory);
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
            <img src="/Navbar.png" className="logo-sidebar" alt="Dehon AI" />
          </div>
        </header>

        <button className="new-chat-btn" onClick={startNewChat}>
          <SquarePen size={20} className="new-chat-icon" /> <span className="new-chat-text">Nova Pesquisa</span>
        </button>

        <div className="search-bar-container">
          <Search size={20} className="search-icon" />
          <input 
            type="text" 
            placeholder="Pesquisar" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="history-search-input"
          />
        </div>

        <div className="history-list">
          <div className="section-label">Recentes</div>
          {conversations.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase())).map(c => (
            <div 
              key={c.id} 
              className={`history-item ${c.id === currentId ? 'active' : ''}`}
              onClick={() => setCurrentId(c.id)}
            >
              <MessageSquare size={14} className="history-item-icon" />
              <span className="history-title">{c.title}</span>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-profile" onClick={handleLogout} title="Clique para sair">
            <div className="avatar">{session.user.email[0].toUpperCase()}</div>
            <span className="username">{session.user.email.split('@')[0]}</span>
            <LogOut size={16} className="settings-icon" />
          </div>
        </div>
      </aside>

      <main className="main-content">
        {!currentId ? (
          <div className="home-layout">
            <header className="top-bar">
               <div className="model-info">
                 <img src="/Navbar.png" className="logo-topbar" alt="Navbar Logo" />
               </div>
               <div className="sync-status">
                 <ShieldCheck size={14} className="status-icon active" />
                 <span>Ambiente Acadêmico</span>
               </div>
            </header>

            <div className="home-content">
               <h1 className="home-greeting">O que posso fazer por você?</h1>
               
               <div className="home-input-wrapper">
                 <div className="input-container huge">
                   <textarea 
                     placeholder="Atribua uma pesquisa sobre o Magistério Dehoniano..." 
                     value={input}
                     onChange={(e) => setInput(e.target.value)}
                     onKeyDown={(e) => {
                       if (e.key === 'Enter' && !e.shiftKey) {
                         e.preventDefault();
                         startNewChatWithInput(input);
                       }
                     }}
                     rows={1}
                     disabled={isStreaming}
                   />
                   <button 
                     className={`send-button ${input.trim() ? 'enabled' : ''}`}
                     onClick={() => startNewChatWithInput(input)}
                     disabled={!input.trim() || isStreaming}
                   >
                     <Send size={20} />
                   </button>
                 </div>
                 
                 <div className="scope-dropdown-container home-scope">
                    <button 
                      className="scope-dropdown-button" 
                      onClick={() => setIsScopeOpen(!isScopeOpen)}
                      type="button"
                    >
                      <span className="scope-dropdown-label">Escopo:</span> {scope}
                      <svg className={`chevron ${isScopeOpen ? 'open' : ''}`} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
                    </button>
                    {isScopeOpen && (
                      <div className="scope-dropdown-menu">
                        {['Geral', 'Espiritualidade e Retiros', 'Social e Político', 'Vida e Biografia', 'Correspondência'].map(s => (
                          <div 
                            key={s} 
                            className={`scope-dropdown-item ${scope === s ? 'selected' : ''}`}
                            onClick={() => { setScope(s); setIsScopeOpen(false); }}
                          >
                            {s}
                          </div>
                        ))}
                      </div>
                    )}
                 </div>
               </div>

               <div className="suggestion-pills">
                 <button className="pill" onClick={() => startNewChatWithInput('Resuma O Catecismo Social')}><FileText size={14} /> Resumo: O Catecismo Social</button>
                 <button className="pill" onClick={() => startNewChatWithInput('O que é a Teologia da Reparação?')}><FileText size={14} /> Teologia da Reparação</button>
                 <button className="pill" onClick={() => startNewChatWithInput('Quais as principais Cartas aos Escolásticos?')}><FileText size={14} /> Cartas aos Escolásticos</button>
               </div>
            </div>
          </div>
        ) : (
          <div className="chat-layout">
            <header className="top-bar">
               <div className="model-info">
                 <img src="/Navbar.png" className="logo-topbar" alt="Navbar Logo" />
               </div>
               <div className="sync-status">
                 <ShieldCheck size={14} className="status-icon active" />
                 <span>Pesquisa em Tempo Real</span>
               </div>
            </header>

            <div className="chat-container" ref={scrollRef}>
              {currentChat?.messages.map((m, idx) => (
                <div key={m.id} className={`message-row ${m.role} animate-slide-up ${m.isGreeting ? 'greeting-row' : ''}`}>
                  <div className="message-container">
                    <div className="message-icon-wrapper">
                      {m.role === 'user' ? (
                        <div className="user-avatar">{session.user.email[0].toUpperCase()}</div>
                      ) : (
                        <div className="bot-avatar">
                          <img src="/Avatar.png" alt="Bot" className="bot-img" />
                        </div>
                      )}
                    </div>
                    <div className="message-body">
                      {m.role === 'user' ? (
                        <div className="user-header">
                          <span className="user-name">Sua Pesquisa</span>
                        </div>
                      ) : (
                        m.metadata ? (
                          <div className="assistant-header">
                            <span className={`badge confidence-${m.metadata.confidence.level.toLowerCase()}`}>
                               Confiança {m.metadata.confidence.level} ({m.metadata.confidence.percentage}%)
                            </span>
                          </div>
                        ) : null
                      )}
                      {m.role === 'assistant' && m.content === '' && isStreaming && idx === currentChat.messages.length - 1 ? (
                        <div className="thinking-container fade-in">
                          <div className="thinking-trace"></div>
                          <div className="thinking-text">Consultando o acervo de Padre Dehon...</div>
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
                                    <span className="source-link">
                                      <span className="ref-label">[{referencedIndices.find(i => m.citations[i].id === cite.id) + 1}]</span>
                                      <span className="source-title">{cite.title}</span>
                                      {cite.sigla && <span className="source-sigla"> · {cite.sigla}</span>}
                                    </span>
                                  </div>
                                  {(cite.destinatario || cite.data) && (
                                    <div className="source-meta">
                                      {cite.destinatario && <span className="source-meta-item"><strong>Para:</strong> {cite.destinatario}</span>}
                                      {cite.data && <span className="source-meta-item"><strong>Data:</strong> {cite.data}</span>}
                                    </div>
                                  )}
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
                  <Send size={20} />
                </button>
              </div>
              
              <div className="scope-dropdown-container">
                {isScopeOpen && (
                  <div className="scope-dropdown-menu">
                    {['Geral', 'Espiritualidade e Retiros', 'Social e Político', 'Vida e Biografia', 'Correspondência'].map(s => (
                      <div 
                        key={s} 
                        className={`scope-dropdown-item ${scope === s ? 'selected' : ''}`}
                        onClick={() => { setScope(s); setIsScopeOpen(false); }}
                      >
                        {s}
                      </div>
                    ))}
                  </div>
                )}
                <button 
                  className="scope-dropdown-button" 
                  onClick={() => setIsScopeOpen(!isScopeOpen)}
                  type="button"
                >
                  <span className="scope-dropdown-label">Escopo:</span> {scope}
                  <svg className={`chevron ${isScopeOpen ? 'open' : ''}`} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
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
