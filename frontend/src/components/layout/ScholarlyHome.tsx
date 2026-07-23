import React from 'react';
import './ScholarlyHome.css';
import { FileText, Sparkles, MessageCircle, BookOpen, Scroll, RefreshCw, Compass } from 'lucide-react';
import ChatInput from '../chat/ChatInput';
import { magneticEffect } from '../../utils/transitions';
import { GooeyText } from '../ui/GooeyText';

import type { UserProfile } from '../ui/ProfileModal';

interface ScholarlyHomeProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  isStreaming: boolean;
  onSuggestionClick: (query: string) => void;
  profile: UserProfile;
}

const ScholarlyHome: React.FC<ScholarlyHomeProps> = ({
  input,
  onInputChange,
  onSend,
  isStreaming,
  onSuggestionClick,
  profile
}) => {
  const suggestionPool = [
    { text: 'Resuma O Catecismo Social', icon: <FileText size={14} />, category: 'Obras' },
    { text: 'O que é a Teologia da Reparação?', icon: <Sparkles size={14} />, category: 'Teologia' },
    { text: 'O que Dehon fala sobre o Reinado Social de Cristo?', icon: <BookOpen size={14} />, category: 'Social' },
    { text: 'Quais os pontos centrais da obra Retraite de Moulins?', icon: <Scroll size={14} />, category: 'Retiros' },
    { text: 'Resuma as impressões de viagem de Dehon à Ásia', icon: <Compass size={14} />, category: 'Viagens' },
    { text: 'Qual era a relação entre Dehon e o Papa Leão XIII?', icon: <MessageCircle size={14} />, category: 'História' },
    { text: 'O que Dehon ensina sobre a adoração eucarística?', icon: <Sparkles size={14} />, category: 'Espiritualidade' },
    { text: 'Quais as origens da Congregação dos Dehonianos em Saint-Quentin?', icon: <BookOpen size={14} />, category: 'Histórico' },
  ];

  const [activeSuggestions, setActiveSuggestions] = React.useState(() => {
    return [...suggestionPool].sort(() => 0.5 - Math.random()).slice(0, 4);
  });
  const [isRotating, setIsRotating] = React.useState(false);

  const handleShuffle = () => {
    setIsRotating(true);
    setTimeout(() => {
      const shuffled = [...suggestionPool].sort(() => 0.5 - Math.random()).slice(0, 4);
      setActiveSuggestions(shuffled);
      setIsRotating(false);
    }, 200);
  };

  const cardsRef = React.useRef<HTMLDivElement[]>([]);

  React.useEffect(() => {
    cardsRef.current.forEach(card => {
      if (card) magneticEffect(card);
    });
  }, [activeSuggestions]);

  const getGreeting = () => {
    const hours = new Date().getHours();
    let period = 'Bom dia';
    if (hours >= 12 && hours < 18) {
      period = 'Boa tarde';
    } else if (hours >= 18 || hours < 5) {
      period = 'Boa noite';
    }

    const userName = profile.name || 'Pesquisador';

    let fullGreeting = '';
    if (profile.title === 'Padre') {
      const suffix = profile.congregation === 'Dehoniano' ? ', scj' : '';
      fullGreeting = `${period}, Padre ${userName}${suffix}`;
    } else if (profile.title === 'Religioso de votos simples') {
      const suffix = profile.congregation === 'Dehoniano' ? ', scj' : '';
      fullGreeting = `${period}, Fr. ${userName}${suffix}`;
    } else {
      fullGreeting = `${period}, ${userName}`;
    }

    return `${fullGreeting}! Como posso ajudar em sua pesquisa hoje?`;
  };

  return (
    <div className="home-container">
      {/* Subtle ambient glow */}
      <div className="home-ambient-glow" />

      <div className="home-hero">
        <h1 className="home-title">Biblioteca Dehoniana</h1>
        <GooeyText
          texts={["Para <strong>tempos novos, obras novas</strong>.", "A inteligência a serviço <strong>do Coração</strong>."]}
          className="home-subtitle-gooey"
          textClassName="home-subtitle-text"
          morphTime={1.2}
          cooldownTime={3.5}
        />
      </div>

      <div className="home-greeting">
        {getGreeting()}
      </div>

      <div className="suggestions-section">
        <div className="suggestions-header">
          <p className="suggestions-label">Sugestões de Pesquisa</p>
          <button 
            className={`shuffle-btn ${isRotating ? 'spinning' : ''}`}
            onClick={handleShuffle}
            title="Girar sugestões de temas"
            aria-label="Girar sugestões de temas"
          >
            <RefreshCw size={13} />
            <span>Girar 🎲</span>
          </button>
        </div>
        <div className="suggestions-grid">
          {activeSuggestions.map((s, idx) => (
            <div
              key={s.text}
              ref={el => { if (el) cardsRef.current[idx] = el; }}
              className="suggestion-card animate-fade-in"
              style={{ animationDelay: `${0.05 + idx * 0.05}s` }}
              onClick={() => onSuggestionClick(s.text)}
              onKeyDown={(e) => e.key === 'Enter' && onSuggestionClick(s.text)}
              role="button"
              tabIndex={0}
              aria-label={`Sugerir pesquisa: ${s.text}`}
            >
              <span className="suggestion-icon">{s.icon}</span>
              <span className="suggestion-text">{s.text}</span>
              <span className="suggestion-category">{s.category}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="home-input-section">
        <ChatInput
          input={input}
          onInputChange={onInputChange}
          onSend={onSend}
          isStreaming={isStreaming}
        />
      </div>

      <footer className="home-footer">
        <div className="identity-badge">
          <span>Sistema de Alta Pesquisa desenvolvido por</span>
          <strong>Fr. João Rodrigues Utxica, scj</strong>
        </div>
      </footer>
    </div>
  );
};

export default ScholarlyHome;
