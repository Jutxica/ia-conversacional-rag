import React, { useState, useEffect } from 'react';
import './index.css';


// Components
import Sidebar from './components/layout/Sidebar';
import ScholarlyHome from './components/layout/ScholarlyHome';

import MessageList from './components/chat/MessageList';
import ChatInput from './components/chat/ChatInput';
import CitationGrid from './components/ui/CitationGrid';
import ProfileModal from './components/ui/ProfileModal';
import type { UserProfile } from './components/ui/ProfileModal';
// Icons
import { PanelLeftClose, PanelLeftOpen, ShieldCheck, Share2, Check, LogOut, X, BookOpen } from 'lucide-react';

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

interface AppProps {
  isAdmin: boolean;
  onSwitchToAdmin: () => void;
}

export default function App({ isAdmin = false, onSwitchToAdmin = () => {} }: AppProps) {
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [scope, setScope] = useState('Geral');
  const [categories, setCategories] = useState<string[]>(['Obras Espirituais', 'Obras Sociais', 'Diários', 'Viagens', 'Correspondência', 'Inéditos e Outros']);

  const handleScopeChange = (newScope: string) => {
    setScope(newScope);
    if (newScope === 'Geral') {
      setCategories(['Obras Espirituais', 'Obras Sociais', 'Diários', 'Viagens', 'Correspondência', 'Inéditos e Outros']);
    } else if (newScope === 'Espiritualidade e Retiros' || newScope === 'Espiritualidade') {
      setCategories(['Obras Espirituais']);
    } else if (newScope === 'Social e Político' || newScope === 'Social') {
      setCategories(['Obras Sociais']);
    } else if (newScope === 'Vida e Biografia' || newScope === 'Biografia') {
      setCategories(['Diários', 'Viagens']);
    } else if (newScope === 'Correspondência' || newScope === 'Correspondencia') {
      setCategories(['Correspondência']);
    }
  };

  const handleCategoriesChange = (newCategories: string[]) => {
    setCategories(newCategories);
    const allCats = ['Obras Espirituais', 'Obras Sociais', 'Diários', 'Viagens', 'Correspondência', 'Inéditos e Outros'];
    if (newCategories.length === allCats.length) {
      setScope('Geral');
    } else if (newCategories.length === 1 && newCategories[0] === 'Obras Espirituais') {
      setScope('Espiritualidade e Retiros');
    } else if (newCategories.length === 1 && newCategories[0] === 'Obras Sociais') {
      setScope('Social e Político');
    } else if (newCategories.length === 2 && newCategories.includes('Diários') && newCategories.includes('Viagens')) {
      setScope('Vida e Biografia');
    } else if (newCategories.length === 1 && newCategories[0] === 'Correspondência') {
      setScope('Correspondência');
    } else {
      setScope('Personalizado');
    }
  };
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

  const [profile, setProfile] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('dehon-profile');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return { name: '', photoUrl: '', title: 'Leigo', congregation: 'Dehoniano' };
  });
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

  
  

  const handleSaveProfile = async (updated: UserProfile) => {
    setProfile(updated);
    localStorage.setItem('dehon-profile', JSON.stringify(updated));
  };




  // --- Actions ---

  const startNewChat = () => {
    setCurrentId(null);
    setInput('');
    setActiveCitationMessageId(null);
    setCurrentConversationId(null);
  };

  const handleDeleteChat = async (chatId: string) => {
    // Remove from local state
    setConversations(prev => prev.filter(c => c.id !== chatId));
    if (currentId === chatId) {
      setCurrentId(null);
      setActiveCitationMessageId(null);
    }
  };


  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'midnight' : 'light');
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
        body: JSON.stringify({ query, scope, history: historyPayload, conversation_id: currentConversationId, categories }),
      });

      if (!response.ok) throw new Error(`Server Error: ${response.status}`);

      const assistantMessageId = (Date.now() + 1).toString();

      // Check if response is standard JSON (like from n8n) instead of SSE stream
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        // n8n Agent typically returns the response in "output" or similar field
        const content = data.output || data.text || data.message || (typeof data === 'string' ? data : JSON.stringify(data));
        
        setConversations(prev => prev.map(c => 
          c.id === chatId 
            ? { ...c, messages: [...c.messages, { id: assistantMessageId, role: 'assistant', content, timestamp: new Date() }] }
            : c
        ));
        setIsStreaming(false);
        return;
      }

      // Existing SSE Streaming logic
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

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
              // Abre automaticamente o painel de citações quando elas chegam (desativado por preferência do usuário)
              // setActiveCitationMessageId(assistantMessageId);
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


  return (
    <div className="app-container">
      {/* Morph Gradient Blur Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-blue-400/20 dark:bg-blue-900/10 blur-[120px] pointer-events-none animate-pulse" style={{ animationDuration: '8s' }} />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-amber-400/20 dark:bg-amber-900/10 blur-[120px] pointer-events-none animate-pulse" style={{ animationDuration: '12s' }} />
      <div className="absolute top-[40%] left-[30%] w-[300px] h-[300px] rounded-full bg-indigo-300/15 dark:bg-indigo-950/5 blur-[100px] pointer-events-none" />
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
        theme={theme}
        onThemeToggle={toggleTheme}
        scope={scope}
        onScopeChange={handleScopeChange}
        categories={categories}
        onCategoriesChange={handleCategoriesChange}
        profile={profile}
        onOpenProfile={() => setIsProfileModalOpen(true)}
      />

      <main className="main-viewport">
        <div className="page-panel">
          <header className="top-nav">
            <button 
              className="menu-toggle" 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              title={isSidebarOpen ? "Recolher barra lateral" : "Expandir barra lateral"}
            >
              {isSidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
            </button>
            <div className="nav-brand" onClick={startNewChat}>
              <img src="/Navbar.png" alt="Dehon AI" />
            </div>
            <div className="nav-actions"></div>
          </header>

          <div className="content-area">
            {!currentId ? (
              <ScholarlyHome
                input={input}
                onInputChange={setInput}
                onSend={handleSend}
                isStreaming={isStreaming}
                onSuggestionClick={(q) => { setInput(q); handleSend(); }}
                profile={profile}
              />
            ) : (
              <div className={`chat-layout-wrapper ${activeMessageWithCitations ? 'has-panel' : ''}`}>
                <div className="chat-interface">
                  <MessageList
                    messages={currentChat.messages}
                    isStreaming={isStreaming}
                                onViewCitations={(msgId) => setActiveCitationMessageId(prev => prev === msgId ? null : msgId)}
                    profile={profile}
                    activeCitationMessageId={activeCitationMessageId}
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

      <ProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        profile={profile}
        onSave={handleSaveProfile}
      />
    </div>
  );
}
