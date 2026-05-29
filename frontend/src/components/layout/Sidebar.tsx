import React, { useState } from 'react';
import './Sidebar.css';
import {
  MessageSquare,
  SquarePen,
  Search,
  LogOut,
  X,
  Moon,
  Sun,
  ShieldCheck,
  ChevronLeft,
  Library,
  BookOpen,
  Clock,
  Trash2,
  Check,
  Settings2,
  Zap,
} from 'lucide-react';
import { magneticEffect } from '../../utils/transitions';
import type { UserProfile } from '../ui/ProfileModal';

interface Conversation {
  id: string;
  title: string;
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  conversations: Conversation[];
  currentId: string | null;
  onSelectChat: (id: string) => void;
  onDeleteChat: (id: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  session: any;
  onLogout: () => void;
  theme: 'light' | 'midnight';
  onThemeToggle: () => void;
  scope: string;
  onScopeChange: (scope: string) => void;
  autoCleanup: { enabled: boolean; maxDays: number; maxCount: number };
  onAutoCleanupChange: (settings: any) => void;
  categories: string[];
  onCategoriesChange: (categories: string[]) => void;
  profile: UserProfile;
  onOpenProfile: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  onNewChat,
  conversations,
  currentId,
  onSelectChat,
  onDeleteChat,
  searchQuery,
  onSearchChange,
  session,
  onLogout,
  theme,
  onThemeToggle,
  scope,
  onScopeChange,
  autoCleanup,
  onAutoCleanupChange,
  categories,
  onCategoriesChange,
  profile,
  onOpenProfile,
}) => {
  const newChatRef = React.useRef<HTMLButtonElement>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [isScopeOpen, setIsScopeOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isCollectionsOpen, setIsCollectionsOpen] = useState(false);

  const availableCategories = [
    'Obras Espirituais',
    'Obras Sociais',
    'Diários',
    'Viagens',
    'Correspondência',
    'Inéditos e Outros'
  ];

  const handleCategoryToggle = (cat: string) => {
    if (categories.includes(cat)) {
      onCategoriesChange(categories.filter(c => c !== cat));
    } else {
      onCategoriesChange([...categories, cat]);
    }
  };

  const selectAllCategories = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onCategoriesChange(availableCategories);
  };

  const clearAllCategories = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onCategoriesChange([]);
  };

  const scopes = [
    'Geral',
    'Espiritualidade e Retiros',
    'Social e Político',
    'Vida e Biografia',
    'Correspondência'
  ];

  React.useEffect(() => {
    if (newChatRef.current) magneticEffect(newChatRef.current);
  }, []);

  const filtered = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const today = filtered.filter((_, i) => i < 3);
  const earlier = filtered.filter((_, i) => i >= 3);

  const handleDeleteClick = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    if (confirmDeleteId === chatId) {
      onDeleteChat(chatId);
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(chatId);
      // Reset confirm state after 3 seconds
      setTimeout(() => setConfirmDeleteId(prev => prev === chatId ? null : prev), 3000);
    }
  };

  const renderChatItem = (c: Conversation) => (
    <div key={c.id} className={`sb-item-row ${c.id === currentId ? 'sb-item-active' : ''}`}>
      <button
        className="sb-item"
        onClick={() => onSelectChat(c.id)}
      >
        <MessageSquare size={13} className="sb-item-icon" />
        <span className="sb-item-label">{c.title}</span>
        {c.id === currentId && <span className="sb-item-dot" />}
      </button>
      <button
        className={`sb-delete-btn ${confirmDeleteId === c.id ? 'sb-delete-confirm' : ''}`}
        onClick={(e) => handleDeleteClick(e, c.id)}
        title={confirmDeleteId === c.id ? 'Clique novamente para confirmar' : 'Apagar conversa'}
        aria-label="Apagar conversa"
      >
        <Trash2 size={13} />
      </button>
    </div>
  );

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && <div className="sb-overlay" onClick={onClose} />}

      <aside className={`sb-root ${isOpen ? 'sb-open' : 'sb-closed'}`}>
        {/* ── Rail (collapse handle) ── */}
        <button
          className="sb-rail"
          onClick={onClose}
          title="Recolher sidebar"
          aria-label="Recolher sidebar"
        >
          <ChevronLeft size={14} />
        </button>

        {/* ── Header ── */}
        <div className="sb-header">
          <div className="sb-brand" onClick={() => window.location.href = '/'}>
            <img src="/Navbar.png" className="sb-logo" alt="Dehon AI" />
          </div>
          <button className="sb-close-mobile" onClick={onClose} aria-label="Fechar menu">
            <X size={18} />
          </button>
        </div>

        {/* ── New Chat Action ── */}
        <div className="sb-actions">
          <button ref={newChatRef} className="sb-new-chat" onClick={onNewChat}>
            <SquarePen size={16} />
            <span>Nova Pesquisa</span>
          </button>
        </div>

        {/* ── Search ── */}
        <div className="sb-search-wrap">
          <Search size={14} className="sb-search-icon" />
          <input
            type="text"
            placeholder="Pesquisar histórico…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="sb-search-input"
          />
        </div>

        {/* ── Content / History ── */}
        <div className="sb-content">
          {filtered.length === 0 ? (
            <div className="sb-empty">
              <BookOpen size={28} className="sb-empty-icon" />
              <p>Nenhuma pesquisa ainda.</p>
              <span>Inicie uma nova consulta acima.</span>
            </div>
          ) : (
            <>
              {today.length > 0 && (
                <div className="sb-group">
                  <div className="sb-group-label">
                    <Clock size={11} />
                    <span>Recentes</span>
                  </div>
                  <div className="sb-menu">
                    {today.map(renderChatItem)}
                  </div>
                </div>
              )}

              {earlier.length > 0 && (
                <div className="sb-group">
                  <div className="sb-group-label">
                    <Library size={11} />
                    <span>Anteriores</span>
                  </div>
                  <div className="sb-menu">
                    {earlier.map(renderChatItem)}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="sb-footer">
          {session ? (
            <>
              {/* Options row */}
              <div className="sb-footer-opts">
                <button
                  className="sb-opt-btn"
                  onClick={onThemeToggle}
                  title={theme === 'midnight' ? 'Modo Claro' : 'Modo Escuro'}
                >
                  {theme === 'midnight' ? <Sun size={15} /> : <Moon size={15} />}
                  <span>{theme === 'midnight' ? 'Tema Claro' : 'Tema Escuro'}</span>
                </button>

                <div className="sb-security">
                  <ShieldCheck size={13} className="sb-security-icon" />
                  <span>Sistema Seguro · TLS</span>
                </div>

                <div className="sb-scope-wrapper">
                  <button 
                    className={`sb-opt-btn sb-scope-trigger ${isScopeOpen ? 'active' : ''}`}
                    onClick={() => setIsScopeOpen(!isScopeOpen)}
                  >
                    <span className="sb-badge-dot" />
                    <span style={{ flex: 1 }}>{scope}</span>
                    <BookOpen size={12} style={{ opacity: 0.6 }} />
                  </button>
                  
                  {isScopeOpen && (
                    <div className="sb-scope-dropdown">
                      <div className="sb-scope-header">Sistema de Alta Pesquisa</div>
                      {scopes.map(s => (
                        <button
                          key={s}
                          className={`sb-scope-item ${scope === s ? 'selected' : ''}`}
                          onClick={() => {
                            onScopeChange(s);
                            setIsScopeOpen(false);
                          }}
                        >
                          {s}
                          {scope === s && <Check size={12} />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="sb-collections-wrapper">
                  <button 
                    className={`sb-opt-btn sb-collections-trigger ${isCollectionsOpen ? 'active' : ''}`}
                    onClick={() => setIsCollectionsOpen(!isCollectionsOpen)}
                  >
                    <Library size={15} />
                    <span style={{ flex: 1 }}>Coleções ({categories.length})</span>
                    <Settings2 size={12} style={{ opacity: 0.6 }} />
                  </button>
                  
                  {isCollectionsOpen && (
                    <div className="sb-collections-dropdown">
                      <div className="sb-collections-header">
                        <span>Coleções de Obras</span>
                        <div className="sb-collections-actions">
                          <button onClick={selectAllCategories} className="sb-action-link">Todas</button>
                          <span style={{ opacity: 0.3, fontSize: '9px', margin: '0 4px', color: 'var(--text-muted)' }}>|</span>
                          <button onClick={clearAllCategories} className="sb-action-link">Limpar</button>
                        </div>
                      </div>
                      <div className="sb-collections-list">
                        {availableCategories.map(cat => {
                          const isChecked = categories.includes(cat);
                          return (
                            <label key={cat} className="sb-collection-checkbox-item">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => handleCategoryToggle(cat)}
                                className="sb-checkbox"
                              />
                              <span className="sb-checkbox-label">{cat}</span>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                <button className="sb-opt-btn sb-opt-logout" onClick={onLogout}>
                  <LogOut size={15} />
                  <span>Sair da Conta</span>
                </button>

                <div className="sb-settings-wrapper">
                  <button 
                    className={`sb-opt-btn sb-settings-trigger ${isSettingsOpen ? 'active' : ''}`}
                    onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                  >
                    <Settings2 size={15} />
                    <span>Gestão de Histórico</span>
                    <Zap size={12} className={autoCleanup.enabled ? 'sb-cleanup-active' : ''} />
                  </button>

                  {isSettingsOpen && (
                    <div className="sb-settings-dropdown">
                      <div className="sb-settings-header">Configurações Locais</div>
                      <div className="sb-setting-item">
                        <label className="sb-switch-label">
                          <span>Limpeza Automática</span>
                          <input 
                            type="checkbox" 
                            checked={autoCleanup.enabled} 
                            onChange={(e) => onAutoCleanupChange({ ...autoCleanup, enabled: e.target.checked })}
                          />
                        </label>
                      </div>
                      {autoCleanup.enabled && (
                        <>
                          <div className="sb-setting-info">
                            Mantém os últimos {autoCleanup.maxCount} chats ou {autoCleanup.maxDays} dias.
                          </div>
                          <div className="sb-setting-input-group">
                            <label>Máximo de Chats:</label>
                            <input 
                              type="number" 
                              value={autoCleanup.maxCount}
                              onChange={(e) => onAutoCleanupChange({ ...autoCleanup, maxCount: parseInt(e.target.value) || 1 })}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* User profile */}
              <div className="sb-user" onClick={onOpenProfile} style={{ cursor: 'pointer' }} title="Clique para configurar o perfil">
                <div className="sb-avatar">
                  {profile.photoUrl ? (
                    <img src={profile.photoUrl} alt={profile.name} className="sb-avatar-img" />
                  ) : (
                    profile.name ? profile.name[0].toUpperCase() : session.user.email[0].toUpperCase()
                  )}
                </div>
                <div className="sb-user-info">
                  <span className="sb-user-name">
                    {profile.title === 'Padre' && (profile.congregation === 'Dehoniano' ? `Pe. ${profile.name}, scj` : `Padre ${profile.name}`)}
                    {profile.title === 'Religioso de votos simples' && (profile.congregation === 'Dehoniano' ? `Fr. ${profile.name}, scj` : `Fr. ${profile.name}`)}
                    {profile.title === 'Leigo' && (profile.name || session.user.email.split('@')[0])}
                  </span>
                  <span className="sb-user-email">{session.user.email}</span>
                </div>
              </div>
            </>
          ) : (
            <button className="sb-login-prompt" onClick={() => window.location.reload()}>
              <LogOut size={16} />
              <span>Entrar na Biblioteca</span>
            </button>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
