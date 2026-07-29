import React from 'react';
import './ScholarlyHome.css';
import ChatInput from '../chat/ChatInput';
import { GooeyText } from '../ui/GooeyText';

import type { UserProfile } from '../ui/ProfileModal';
import { translations } from '../../i18n/translations';

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
  profile
}) => {
  const lang = profile.language || 'pt';
  const t = translations[lang] || translations['pt'];

  const getGreeting = () => {
    const hours = new Date().getHours();
    let period = t.greetingMorning;
    if (hours >= 12 && hours < 18) {
      period = t.greetingAfternoon;
    } else if (hours >= 18 || hours < 5) {
      period = t.greetingEvening;
    }

    const userName = profile.name || t.researcherTitle;

    let fullGreeting = '';
    if (profile.title === 'Padre') {
      const suffix = profile.congregation === 'Dehoniano' ? ', scj' : '';
      fullGreeting = `${period}, ${t.fatherTitle} ${userName}${suffix}`;
    } else if (profile.title === 'Religioso de votos simples') {
      const suffix = profile.congregation === 'Dehoniano' ? ', scj' : '';
      fullGreeting = `${period}, ${t.brotherTitle} ${userName}${suffix}`;
    } else {
      fullGreeting = `${period}, ${userName}`;
    }

    return `${fullGreeting}! ${t.greetingQuestion}`;
  };

  return (
    <div className="home-container">
      {/* Subtle ambient glow */}
      <div className="home-ambient-glow" />

      <div className="home-hero">
        <h1 className="home-title">{t.homeTitle}</h1>
        <GooeyText
          texts={[t.homeSubtitle1, t.homeSubtitle2]}
          className="home-subtitle-gooey"
          textClassName="home-subtitle-text"
          morphTime={1.2}
          cooldownTime={3.5}
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
          placeholder={t.inputPlaceholder}
        />
      </div>

      <footer className="home-footer">
        <div className="identity-badge">
          <span>{t.footerDeveloper}</span>
          <strong>Fr. João Rodrigues Utxica, scj</strong>
        </div>
      </footer>
    </div>
  );
};

export default ScholarlyHome;

