import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import { MessageSquare, Send, ShieldCheck, FileText, LogOut, SquarePen, Search, Menu, X, Share2, Check, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { supabase } from './supabaseClient';

// --- Types ---
interface Citation {
  id: string | number;
  title: string;
  url?: string;
  page_url?: string;
  page_number?: string | number;
  snippet?: string;
  sigla?: string;
  destinatario?: string;
  data?: string;
  score?: number;
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
  is_public?: boolean;
  user_id?: string;
}

// --- Components ---
const LoginPage = () => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [countryCode, setCountryCode] = useState('+55');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const countries = [
    { code: '+55', flag: '🇧🇷', name: 'Brasil' },
    { code: '+39', flag: '🇮🇹', name: 'Itália' },
    { code: '+33', flag: '🇫🇷', name: 'França' },
    { code: '+49', flag: '🇩🇪', name: 'Alemanha' },
    { code: '+1', flag: '🇺🇸', name: 'EUA/Canadá' },
    { code: '+34', flag: '🇪🇸', name: 'Espanha' },
    { code: '+351', flag: '🇵🇹', name: 'Portugal' },
    { code: '+54', flag: '🇦🇷', name: 'Argentina' },
    { code: '+57', flag: '🇨🇴', name: 'Colômbia' },
    { code: '+56', flag: '🇨🇱', name: 'Chile' },
    { code: '+52', flag: '🇲🇽', name: 'México' },
    { code: '+48', flag: '🇵🇱', name: 'Polônia' },
    { code: '+32', flag: '🇧🇪', name: 'Bélgica' },
    { code: '+41', flag: '🇨🇭', name: 'Suíça' },
    { code: '+43', flag: '🇦🇹', name: 'Áustria' },
    { code: '+31', flag: '🇳🇱', name: 'Holanda' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (mode === 'signup') {
      if (password !== confirmPassword) {
        setError('As senhas não coincidem.');
        setLoading(false);
        return;
      }
      if (password.length < 6) {
        setError('A senha deve ter pelo menos 6 caracteres.');
        setLoading(false);
        return;
      }
      
      const { error } = await supabase.auth.signUp({ 
        email, 
        password,
        options: {
          data: {
            full_name: fullName,
            phone: `${countryCode} ${phone}`
          }
        }
      });

      if (error) {
        setError(error.message === 'User already registered' ? 'Este e-mail já está cadastrado.' : 'Erro ao criar conta. Tente novamente.');
      } else {
        setSuccess('Conta criada! Você já pode acessar a biblioteca.');
      }
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setError('Credenciais inválidas. Verifique seu e-mail e senha.');
      }
    }
    setLoading(false);
  };

  return (
    <div className="login-overlay">
      <div className="login-card">
        <img src="/Login.png" className="login-logo" alt="Dehon AI" />
        <h2>Biblioteca Dehoniana</h2>
        <p>{mode === 'login' ? 'Entre na sua conta de pesquisador.' : 'Crie sua conta e comece a pesquisar.'}</p>
        
        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(null); setSuccess(null); }}
            type="button"
          >Entrar</button>
          <button
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => { setMode('signup'); setError(null); setSuccess(null); }}
            type="button"
          >Criar Conta</button>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <>
              <div className="input-group">
                <label>Nome Completo</label>
                <input 
                  type="text" 
                  className="login-input" 
                  placeholder="Seu nome" 
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label>Telefone</label>
                <div className="phone-input-container">
                  <select 
                    className="country-select"
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                  >
                    {countries.sort((a, b) => a.name.localeCompare(b.name)).map(c => (
                      <option key={c.code} value={c.code}>
                        {c.flag} {c.code}
                      </option>
                    ))}
                  </select>
                  <input 
                    type="tel" 
                    className="login-input" 
                    placeholder="Número" 
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </div>
              </div>
            </>
          )}
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
            <label>Senha</label>
            <input 
              type="password" 
              className="login-input" 
              placeholder="••••••••" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {mode === 'signup' && (
            <div className="input-group">
              <label>Confirmar Senha</label>
              <input 
                type="password" 
                className="login-input" 
                placeholder="••••••••" 
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          )}
          {error && <div className="auth-message error">{error}</div>}
          {success && <div className="auth-message success">{success}</div>}
          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? <Loader2 className="animate-spin" /> : <ShieldCheck size={18} />}
            {loading ? (mode === 'login' ? 'Autenticando...' : 'Criando conta...') : (mode === 'login' ? 'Acessar Biblioteca' : 'Criar Conta')}
          </button>
        </form>
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
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAppLoading, setIsAppLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    // Detectar Chat Compartilhado na URL (?chat=ID)
    const urlParams = new URLSearchParams(window.location.search);
    const sharedChatId = urlParams.get('chat');
    if (sharedChatId) {
      loadSharedChat(sharedChatId);
    }

    // Finaliza a Splash Screen após um breve delay para garantir imersão
    const timer = setTimeout(() => {
      setIsAppLoading(false);
    }, 3000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timer);
    };
  }, []);

  const loadSharedChat = async (id: string) => {
    const { data, error } = await supabase
      .from('chats')
      .select('*')
      .eq('id', id)
      .single();

    if (data && !error) {
      const sanitized = {
        ...data,
        messages: data.messages.map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) }))
      };
      setConversations(prev => {
        if (prev.find(c => c.id === id)) return prev;
        return [sanitized, ...prev];
      });
      setCurrentId(id);
    }
  };

  // Persistência: Carregar do Supabase quando a sessão mudar
  useEffect(() => {
    async function loadChats() {
      if (session?.user?.id) {
        const { data, error } = await supabase
          .from('chats')
          .select('*')
          .eq('user_id', session.user.id)
          .order('updated_at', { ascending: false });

        if (error) {
          console.error("Erro ao carregar histórico do Supabase:", error);
          return;
        }

        if (data) {
          const sanitized = data.map((c: any) => ({
            id: c.id,
            title: c.title,
            messages: c.messages.map((m: any) => ({
              ...m,
              timestamp: new Date(m.timestamp)
            }))
          }));
          setConversations(sanitized);
          // Removido o auto-set do currentId para sempre iniciar na tela vazia (home)
        }
      } else {
        setConversations([]);
        setCurrentId(null);
      }
    }
    loadChats();
  }, [session?.user?.id]);

  // Função auxiliar para salvar chat no Supabase
  const persistChat = async (chat: Conversation) => {
    if (!session?.user?.id) return;
    
    const { error } = await supabase
      .from('chats')
      .upsert({
        id: chat.id,
        user_id: session.user.id,
        title: chat.title,
        messages: chat.messages,
        is_public: chat.is_public || false,
        updated_at: new Date().toISOString()
      });

    if (error) console.error("Erro ao salvar chat no Supabase:", error);
  };

  const toggleShare = async () => {
    if (!currentChat || !session || currentChat.user_id !== session.user.id) return;
    
    const newPublicStatus = !currentChat.is_public;
    
    const { error } = await supabase
      .from('chats')
      .update({ is_public: newPublicStatus })
      .eq('id', currentChat.id);

    if (!error) {
      setConversations(prev => prev.map(c => 
        c.id === currentChat.id ? { ...c, is_public: newPublicStatus } : c
      ));
      
      if (newPublicStatus) {
        const shareUrl = `${window.location.origin}${window.location.pathname}?chat=${currentChat.id}`;
        navigator.clipboard.writeText(shareUrl);
        alert("Link de pesquisa copiado! Agora qualquer pessoa com o link pode visualizar esta conversa.");
      }
    }
  };

  const currentChat = conversations.find(c => c.id === currentId);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentChat?.messages, isStreaming]);

  const startNewChat = () => {
    const newChat: Conversation = {
      id: Date.now().toString() + '_chat',
      title: 'Nova Pesquisa',
      messages: []
    };
    setConversations([newChat, ...conversations]);
    setCurrentId(newChat.id);
  };

  const executeChatLogic = async (chatId: string, query: string, currentHistory: Message[]) => {
    setIsStreaming(true);
    setGlobalError(null);
    setInput('');

    try {
      const historyPayload = currentHistory.map(m => ({ role: m.role, content: m.content }));
      
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/chat';
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, scope: scope, history: historyPayload }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Erro do Servidor (${response.status}): ${errorData}`);
      }

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
              // Salva o estado final da conversa no Supabase ao terminar o streaming
              setConversations(prev => {
                const final = prev.find(c => c.id === chatId);
                if (final) persistChat(final);
                return prev;
              });
            }
          }
        }
      }
    } catch (err) {
      console.error('Erro ao conectar com o backend:', err);
      const errorMsg = 'Falha na conexão com o servidor Dehon AI. Verifique se o backend está rodando.';
      
      setConversations(prev => prev.map(c => 
        c.id === chatId 
          ? { 
              ...c, 
              messages: c.messages.map(m => 
                m.id === assistantMessageId ? { ...m, content: errorMsg } : m
              ) 
            }
          : c
      ));
      
      setIsStreaming(false);
    }
  };

  const startNewChatWithInput = (query: string) => {
    if (!query.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };

    const newChatId = (Date.now() + 1).toString() + '_chat';
    const newChat: Conversation = {
      id: newChatId,
      title: query.slice(0, 30),
      messages: [userMessage]
    };
    
    setConversations([newChat, ...conversations]);
    setCurrentId(newChatId);
    
    executeChatLogic(newChatId, query, [userMessage]);
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
    
    // Salva a mensagem do usuário imediatamente
    persistChat({ ...targetChat, messages: [...targetChat.messages, userMessage] });
    
    executeChatLogic(currentId, query, currentHistory);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  if (isAppLoading) {
    return (
      <div className="splash-screen">
        <div className="splash-content">
          <img src="/Navbar.png" className="splash-logo" alt="Dehon AI" />
          <div className="splash-loader">
            <div className="loader-bar"></div>
          </div>
          <p className="splash-text">Iniciando Ambiente Acadêmico...</p>
        </div>
      </div>
    );
  }

  if (!session && !currentChat?.is_public) {
    return <LoginPage />;
  }

  return (
    <div className="app-container">
      <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <button className="sidebar-close-btn" onClick={() => setIsSidebarOpen(false)}>
          <X size={24} />
        </button>
        <header className="sidebar-header">
          <div className="brand">
            <img src="/Navbar.png" className="logo-sidebar" alt="Dehon AI" />
          </div>
        </header>

        <button className="new-chat-btn" onClick={() => { startNewChat(); setIsSidebarOpen(false); }}>
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
               onClick={() => { setCurrentId(c.id); setIsSidebarOpen(false); }}
            >
              <MessageSquare size={14} className="history-item-icon" />
              <span className="history-title">{c.title}</span>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          {session ? (
            <div className="user-profile" onClick={handleLogout} title="Clique para sair">
              <div className="avatar">{session.user.email[0].toUpperCase()}</div>
              <span className="username">{session.user.email.split('@')[0]}</span>
              <LogOut size={16} className="settings-icon" />
            </div>
          ) : (
            <div className="user-profile" onClick={() => window.location.reload()}>
              <span className="username">Entrar para salvar</span>
            </div>
          )}
        </div>
      </aside>

      <main className="main-content">
        {!currentId ? (
          <div className="home-layout">
            <header className="top-bar">
               <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(true)}>
                 <Menu size={24} />
               </button>
               <div className="model-info logo-clickable" onClick={() => setCurrentId(null)}>
                 <img src="/Navbar.png" className="logo-topbar" alt="Navbar Logo" />
               </div>
               <div className="sync-status">
                 <ShieldCheck size={14} className="status-icon active" />
                 <span>Ambiente Acadêmico</span>
               </div>
               {session && (
                 <button className="header-logout-btn" onClick={handleLogout} title="Sair">
                   <LogOut size={18} />
                   <span>Sair</span>
                 </button>
               )}
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
               <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(true)}>
                 <Menu size={24} />
               </button>
                <div className="model-info logo-clickable" onClick={() => setCurrentId(null)}>
                  <img src="/Navbar.png" className="logo-topbar" alt="Navbar Logo" />
                </div>
                <div className="chat-actions">
                  {currentChat && session && currentChat.user_id === session.user.id && (
                    <button 
                      className={`action-btn share-btn ${currentChat.is_public ? 'active' : ''}`} 
                      onClick={toggleShare}
                      title={currentChat.is_public ? "Pesquisa Pública (Clique para tornar privada)" : "Compartilhar Pesquisa"}
                    >
                      {currentChat.is_public ? <Check size={18} /> : <Share2 size={18} />}
                      <span className="btn-text-desktop">{currentChat.is_public ? "Compartilhado" : "Compartilhar"}</span>
                    </button>
                  )}
                  <div className="sync-status">
                    <ShieldCheck size={14} className="status-icon active" />
                    <span>Pesquisa em Tempo Real</span>
                  </div>
                  {session && (
                    <button className="header-logout-btn" onClick={handleLogout} title="Sair">
                      <LogOut size={18} />
                      <span>Sair</span>
                    </button>
                  )}
                </div>
            </header>

            {/* Banner de Erro Global */}
            {conversations.length > 0 && (
              <div className="global-error-container">
                {currentId && conversations.find(c => c.id === currentId)?.messages.some(m => m.content.includes("Falha na conexão")) && (
                  <div className="error-banner">
                    Falha ao conectar com o Dehon AI. Verifique se o servidor está online.
                  </div>
                )}
              </div>
            )}

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

                      {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                        <div className="citations-section">
                          <div className="section-divider"></div>
                          <div className="sources-header">Evidências Documentais:</div>
                          <div className="sources-list">
                            {m.citations.map((cite, cIdx) => (
                              <div key={cIdx} className={`source-item stagger-${Math.min(cIdx + 1, 5)}`}>
                                <div className="source-reference">
                                  <span className="source-link">
                                    <span className="ref-label">[{cIdx + 1}]</span>
                                    <span className="source-title">{cite.title}</span>
                                    {cite.sigla && <span className="source-sigla"> · {cite.sigla}</span>}
                                    {cite.page_number && <span className="source-sigla"> · p. {cite.page_number}</span>}
                                  </span>
                                  {(cite.page_url || cite.url) && (
                                    <a
                                      href={cite.page_url || cite.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="source-open-link"
                                      title="Abrir fonte original em nova aba"
                                    >
                                      <ExternalLink size={13} /> Ver página
                                    </a>
                                  )}
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
                      )}
                    </div>
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
