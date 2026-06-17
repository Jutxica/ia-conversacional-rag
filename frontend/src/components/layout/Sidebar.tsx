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
  theme: 'light' | 'midnight';
  onThemeToggle: () => void;
  scope: string;
  onScopeChange: (scope: string) => void;

  categories: string[];
  onCategoriesChange: (categories: string[]) => void;
  profile: UserProfile;
  onOpenProfile: () => void;
  autoCleanup: { enabled: boolean; limit: number; type: 'days' | 'count' };
  onAutoCleanupChange: (settings: any) => void;
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
  theme,
  onThemeToggle,
  scope,
  onScopeChange,
  categories,
  onCategoriesChange,
  profile,
  onOpenProfile,
  autoCleanup,
  onAutoCleanupChange,
}) => {
  const newChatRef = React.useRef<HTMLButtonElement>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isScopeOpen, setIsScopeOpen] = useState(false);
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



              </div>

              <div className="sb-settings-wrapper" style={{ position: 'relative', marginTop: '12px' }}>
              <button 
                className={`sb-opt-btn sb-settings-trigger ${isSettingsOpen ? 'active' : ''}`}
                onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', borderRadius: '6px' }}
              >
                <Settings2 size={15} />
                <span style={{ flex: 1, textAlign: 'left', fontSize: '13px' }}>Gestão de Histórico</span>
                <Zap size={12} className={autoCleanup.enabled ? 'sb-cleanup-active' : ''} style={{ color: autoCleanup.enabled ? '#eab308' : 'inherit' }} />
              </button>

              {isSettingsOpen && (
                <div className="sb-settings-dropdown" style={{ position: 'absolute', bottom: '100%', left: '0', width: '220px', background: 'var(--surface-sunken)', border: '1px solid var(--border)', borderRadius: '8px', padding: '12px', marginBottom: '8px', zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                  <div className="sb-settings-header" style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Configurações Locais</div>
                  
                  <div className="sb-setting-item" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Limpeza Automática</span>
                    <input 
                      type="checkbox" 
                      checked={autoCleanup.enabled} 
                      onChange={(e) => onAutoCleanupChange({ ...autoCleanup, enabled: e.target.checked })}
                      style={{ cursor: 'pointer' }}
                    />
                  </div>
                  
                  {autoCleanup.enabled && (
                    <div className="sb-setting-input-group" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Tipo:</span>
                        <select 
                          value={autoCleanup.type}
                          onChange={(e) => onAutoCleanupChange({ ...autoCleanup, type: e.target.value })}
                          style={{ fontSize: '12px', padding: '2px 4px', background: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '4px' }}
                        >
                          <option value="days">Dias</option>
                          <option value="count">Conversas</option>
                        </select>
                      </div>
                      
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Limite:</span>
                        <input 
                          type="number" 
                          value={autoCleanup.limit}
                          onChange={(e) => onAutoCleanupChange({ ...autoCleanup, limit: parseInt(e.target.value) || 1 })}
                          style={{ width: '60px', fontSize: '12px', padding: '2px 4px', background: 'var(--bg-primary)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '4px' }}
                        />
                      </div>
                      
                      <div className="sb-setting-info" style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>
                        Mantém {autoCleanup.type === 'count' ? `os últimos ${autoCleanup.limit} chats` : `chats dos últimos ${autoCleanup.limit} dias`}.
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* User profile */}
              <div className="sb-user" onClick={onOpenProfile} style={{ cursor: 'pointer' }} title="Clique para configurar o perfil">
                <div className="sb-avatar">
                  {profile.photoUrl ? (
                    <img src={profile.photoUrl} alt={profile.name} className="sb-avatar-img" />
                  ) : (
                    profile.name ? profile.name[0].toUpperCase() : 'P'
                  )}
                </div>
                <div className="sb-user-info">
                  <span className="sb-user-name">
                    {profile.title === 'Padre' && (profile.congregation === 'Dehoniano' ? `Pe. ${profile.name}, scj` : `Padre ${profile.name}`)}
                    {profile.title === 'Religioso de votos simples' && (profile.congregation === 'Dehoniano' ? `Fr. ${profile.name}, scj` : `Fr. ${profile.name}`)}
                    {profile.title === 'Leigo' && (profile.name || 'Pesquisador')}
                  </span>
                  <span className="sb-user-email">Usuário Visitante</span>
                </div>
              </div>
            </>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
