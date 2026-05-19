import React, { useState, useEffect } from 'react';
import './index.css';
import { supabase } from './supabaseClient';

// Components
import Sidebar from './components/layout/Sidebar';
import ScholarlyHome from './components/layout/ScholarlyHome';
import LoginPage from './components/layout/LoginPage';
import MessageList from './components/chat/MessageList';
import ChatInput from './components/chat/ChatInput';
import CitationGrid from './components/ui/CitationGrid';
// Icons
import { Menu, ShieldCheck, Share2, Check, LogOut, X, BookOpen } from 'lucide-react';

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
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  is_public?: boolean;
  user_id?: string;
}

export default function App() {
  const [session, setSession] = useState<any>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [scope, setScope] = useState('Geral');
  const [isStreaming, setIsStreaming] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Sidebar aberta por padrão conforme pedido
  const [isAppLoading, setIsAppLoading] = useState(true);
  const [theme, setTheme] = useState<'light' | 'midnight'>((localStorage.getItem('dehon-theme') as any) || 'light');
  const [activeCitationMessageId, setActiveCitationMessageId] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [autoCleanup, setAutoCleanup] = useState(() => {
    const saved = localStorage.getItem('dehon-auto-cleanup');
    return saved ? JSON.parse(saved) : { enabled: true, maxDays: 30, maxCount: 50 };
  });

  useEffect(() => {
    localStorage.setItem('dehon-auto-cleanup', JSON.stringify(autoCleanup));
  }, [autoCleanup]);

  // --- Auth & Session ---
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('dehon-theme', theme);
  }, [theme]);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    const urlParams = new URLSearchParams(window.location.search);
    const sharedChatId = urlParams.get('chat');
    if (sharedChatId) loadSharedChat(sharedChatId);

    const timer = setTimeout(() => setIsAppLoading(false), 2000);
    return () => {
      subscription.unsubscribe();
      clearTimeout(timer);
    };
  }, []);

  // --- Load History ---
  useEffect(() => {
    async function loadChats() {
      if (session?.user?.id) {
        const { data, error } = await supabase
          .from('chats')
          .select('*')
          .eq('user_id', session.user.id)
          .order('updated_at', { ascending: false });

        if (!error && data) {
          const sanitized = data.map((c: any) => ({
            id: c.id,
            title: c.title,
            messages: c.messages.map((m: any) => ({
              ...m,
              timestamp: new Date(m.timestamp)
            })),
            is_public: c.is_public
          }));
          setConversations(sanitized);
        }
      } else {
        setConversations([]);
        setCurrentId(null);
      }
    }
    loadChats();
  }, [session?.user?.id]);

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
      setConversations(prev => [sanitized, ...prev.filter(c => c.id !== id)]);
      setCurrentId(id);
    }
  };

  const persistChat = async (chat: Conversation) => {
    if (!session?.user?.id) return;
    await supabase.from('chats').upsert({
      id: chat.id,
      user_id: session.user.id,
      title: chat.title,
      messages: chat.messages,
      is_public: chat.is_public || false,
      updated_at: new Date().toISOString()
    });
  };

  // --- Actions ---
  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  const startNewChat = () => {
    setCurrentId(null);
    setInput('');
    setActiveCitationMessageId(null);
    setCurrentConversationId(null);
  };

  const handleDeleteChat = async (chatId: string) => {
    // Remove from Supabase
    if (session?.user?.id) {
      await supabase.from('chats').delete().eq('id', chatId).eq('user_id', session.user.id);
    }
    // Remove from local state
    setConversations(prev => prev.filter(c => c.id !== chatId));
    // If the deleted chat was active, go to home
    if (currentId === chatId) {
      setCurrentId(null);
      setActiveCitationMessageId(null);
    }
  };

  useEffect(() => {
    async function runAutoCleanup() {
      if (!session?.user?.id || !autoCleanup.enabled) return;

      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - autoCleanup.maxDays);

      // Delete conversations older than maxDays
      await supabase
        .from('chats')
        .delete()
        .eq('user_id', session.user.id)
        .lt('updated_at', cutoffDate.toISOString());

      // If still too many, delete the oldest ones beyond the limit
      const { data } = await supabase
        .from('chats')
        .select('id, updated_at')
        .eq('user_id', session.user.id)
        .order('updated_at', { ascending: false });

      if (data && data.length > autoCleanup.maxCount) {
        const toDelete = data.slice(autoCleanup.maxCount).map((c: any) => c.id);
        await supabase
          .from('chats')
          .delete()
          .in('id', toDelete);
      }
    }
    runAutoCleanup();
  }, [session?.user?.id, autoCleanup]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'midnight' : 'light');
  };

  const toggleShare = async () => {
    const currentChat = conversations.find(c => c.id === currentId);
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
        alert("Link de pesquisa copiado!");
      }
    }
  };

  const executeChatLogic = async (chatId: string, query: string, history: Message[]) => {
    setIsStreaming(true);
    setInput('');
    setActiveCitationMessageId(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api/chat';
      
      const historyPayload = history.map(m => ({ role: m.role, content: m.content }));

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${import.meta.env.VITE_API_KEY}`
        },
        body: JSON.stringify({ query, scope, history: historyPayload, conversation_id: currentConversationId }),
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      const assistantMessageId = (Date.now() + 1).toString();

      setConversations(prev => prev.map(c => 
        c.id === chatId 
          ? { ...c, messages: [...c.messages, { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date() }] }
          : c
      ));

      let buffer = '';
      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (let line of lines) {
          line = line.trim();
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'conversation_id') {
              setCurrentConversationId(data.conversation_id || data.content);
            } else if (data.type === 'token') {
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
              // Abre automaticamente o painel de citações quando elas chegam
              setActiveCitationMessageId(assistantMessageId);
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
              setConversations(prev => {
                const final = prev.find(c => c.id === chatId);
                if (final) persistChat(final);
                return prev;
              });
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Connection error:', err);
      const errorMsgId = 'err-' + Date.now().toString();
      setConversations(prev => prev.map(c => 
        c.id === chatId 
          ? { ...c, messages: [...c.messages, { id: errorMsgId, role: 'assistant', content: `**Erro de Conexão:** Não foi possível conectar ao servidor.\n\nSe você está usando o Render, o servidor pode estar em "Cold Start" (demora ~50s para acordar) ou há um bloqueio de CORS. Detalhes técnicos: \`${err.message}\``, timestamp: new Date() }] }
          : c
      ));
      setIsStreaming(false);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    if (!currentId) {
      const newChatId = (Date.now() + 1).toString() + '_chat';
      const newChat: Conversation = {
        id: newChatId,
        title: input.slice(0, 30),
        messages: [userMessage]
      };
      setConversations([newChat, ...conversations]);
      setCurrentId(newChatId);
      executeChatLogic(newChatId, input, [userMessage]);
    } else {
      setConversations(prev => prev.map(c => 
        c.id === currentId ? { ...c, messages: [...c.messages, userMessage] } : c
      ));
      const targetChat = conversations.find(c => c.id === currentId);
      if (targetChat) {
        executeChatLogic(currentId, input, [...targetChat.messages, userMessage]);
      }
    }
  };

  const currentChat = conversations.find(c => c.id === currentId);
  const activeMessageWithCitations = currentChat?.messages.find(m => m.id === activeCitationMessageId);

  // --- Render Logic ---
  if (isAppLoading) {
    return (
      <div className="splash-screen">
        <div className="splash-content">
          <img src="/Navbar.png" className="splash-logo" alt="Dehon AI" />
          <div className="splash-loader"><div className="loader-bar"></div></div>
          <p className="splash-text">Ambiente Acadêmico</p>
        </div>
      </div>
    );
  }

  if (!session && !currentChat?.is_public) {
    return <LoginPage onLoginSuccess={() => window.location.reload()} />;
  }

  return (
    <div className="app-container">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNewChat={startNewChat}
        conversations={conversations}
        currentId={currentId}
        onSelectChat={(id) => { setCurrentId(id); }}
        onDeleteChat={handleDeleteChat}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        session={session}
        onLogout={handleLogout}
        theme={theme}
        onThemeToggle={toggleTheme}
        scope={scope}
        onScopeChange={setScope}
        autoCleanup={autoCleanup}
        onAutoCleanupChange={setAutoCleanup}
      />

      <main className="main-viewport">
        <div className="page-panel">
          <header className="top-nav">
            <button className="menu-toggle" onClick={() => setIsSidebarOpen(!isSidebarOpen)}><Menu size={20} /></button>
            <div className="nav-brand" onClick={startNewChat}>
              <img src="/Navbar.png" alt="Dehon AI" />
            </div>
            <div className="nav-actions">
              {currentChat && session && currentChat.user_id === session.user.id && (
                <button
                  className={`share-btn ${currentChat.is_public ? 'shared' : ''}`}
                  onClick={toggleShare}
                >
                  {currentChat.is_public ? <Check size={16} /> : <Share2 size={16} />}
                  <span>{currentChat.is_public ? 'Compartilhado' : 'Compartilhar'}</span>
                </button>
              )}
            </div>
          </header>

          <div className="content-area">
            {!currentId ? (
              <ScholarlyHome
                input={input}
                onInputChange={setInput}
                onSend={handleSend}
                isStreaming={isStreaming}
                onSuggestionClick={(q) => { setInput(q); handleSend(); }}
              />
            ) : (
              <div className={`chat-layout-wrapper ${activeMessageWithCitations ? 'has-panel' : ''}`}>
                <div className="chat-interface">
                  <MessageList
                    messages={currentChat.messages}
                    isStreaming={isStreaming}
                    session={session}
                    onViewCitations={(msgId) => setActiveCitationMessageId(msgId)}
                  />
                  <div className="input-zone">
                    <ChatInput
                      input={input}
                      onInputChange={setInput}
                      onSend={handleSend}
                      isStreaming={isStreaming}
                    />
                  </div>
                </div>

                {activeMessageWithCitations && (
                  <aside className="side-panel animate-slide-left">
                    <div className="side-panel-header">
                      <div className="panel-title">
                        <BookOpen size={18} />
                        <span>Referências da Resposta</span>
                      </div>
                      <button className="close-panel-btn" onClick={() => setActiveCitationMessageId(null)}>
                        <X size={18} />
                      </button>
                    </div>
                    <div className="side-panel-content">
                      <CitationGrid citations={activeMessageWithCitations.citations || []} variant="sidebar" />
                    </div>
                  </aside>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

    </div>
  );
}
