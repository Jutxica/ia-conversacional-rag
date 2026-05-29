import React from 'react';
import './ScholarlyHome.css';
import { FileText, Sparkles, MessageCircle, BookOpen, Scroll } from 'lucide-react';
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
  const suggestions = [
    { text: 'Resuma O Catecismo Social', icon: <FileText size={16} />, category: 'Obras' },
    { text: 'O que é a Teologia da Reparação?', icon: <Sparkles size={16} />, category: 'Teologia' },
    { text: 'Principais Cartas aos Escolásticos', icon: <MessageCircle size={16} />, category: 'Epistolário' },
    { text: 'Qual a espiritualidade do Coração?', icon: <BookOpen size={16} />, category: 'Espiritualidade' },
    { text: 'Contexto do Diário de Dehon', icon: <Scroll size={16} />, category: 'Diário' },
  ];

  const cardsRef = React.useRef<HTMLDivElement[]>([]);

  React.useEffect(() => {
    cardsRef.current.forEach(card => {
      if (card) magneticEffect(card);
    });
  }, []);

  const getGreeting = () => {
    const hours = new Date().getHours();
    let period = 'Bom dia';
    if (hours >= 12 && hours < 18) {
      period = 'Boa tarde';
    } else if (hours >= 18 || hours < 5) {
      period = 'Boa noite';
    }

    const userName = profile.name || 'Pesquisador';

    if (profile.title === 'Padre') {
      const suffix = profile.congregation === 'Dehoniano' ? ', scj' : '';
      return `${period}, Padre ${userName}${suffix}`;
    } else if (profile.title === 'Religioso de votos simples') {
      const suffix = profile.congregation === 'Dehoniano' ? ', scj' : '';
      return `${period}, Fr. ${userName}${suffix}`;
    } else {
      return `${period}, ${userName}`;
    }
  };

  return (
    <div className="home-container">
      {/* Subtle ambient glow */}
      <div className="home-ambient-glow" />

      <div className="home-hero">
        <h1 className="home-title">Biblioteca Dehoniana</h1>
        <GooeyText
          texts={["Para tempos novos,", "obras novas."]}
          className="home-subtitle-gooey"
          textClassName="home-subtitle-text"
          morphTime={1.2}
          cooldownTime={2.5}
        />
      </div>

      <div className="home-greeting">
        {getGreeting()}
      </div>

      <div className="home-input-section">
        <ChatInput
          input={input}
          onInputChange={onInputChange}
          onSend={onSend}
          isStreaming={isStreaming}
        />
      </div>

      <div className="suggestions-section">
        <p className="suggestions-label">Sugestões de Pesquisa</p>
        <div className="suggestions-grid">
          {suggestions.map((s, idx) => (
            <div
              key={idx}
              ref={el => { if (el) cardsRef.current[idx] = el; }}
              className="suggestion-card animate-fade-in"
              style={{ animationDelay: `${0.15 + idx * 0.08}s` }}
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
