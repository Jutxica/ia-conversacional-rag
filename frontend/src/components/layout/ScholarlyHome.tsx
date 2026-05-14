import React from 'react';
import './ScholarlyHome.css';
import { FileText, Sparkles, MessageCircle, BookOpen, Scroll } from 'lucide-react';
import ChatInput from '../chat/ChatInput';
import { magneticEffect } from '../../utils/transitions';

interface ScholarlyHomeProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  isStreaming: boolean;
  onSuggestionClick: (query: string) => void;
}

const ScholarlyHome: React.FC<ScholarlyHomeProps> = ({
  input,
  onInputChange,
  onSend,
  isStreaming,
  onSuggestionClick
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

  return (
    <div className="home-container">
      {/* Subtle ambient glow */}
      <div className="home-ambient-glow" />

      <div className="home-hero">
        <h1 className="home-title">Biblioteca Dehoniana</h1>
        <p className="home-subtitle">"Sint unum: A inteligência a serviço do Coração."</p>
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
