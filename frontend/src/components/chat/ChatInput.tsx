import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';
import { Send, ChevronUp, BookOpen } from 'lucide-react';
import { magneticEffect } from '../../utils/transitions';

interface ChatInputProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  scope: string;
  onScopeChange: (scope: string) => void;
  isStreaming: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  onInputChange,
  onSend,
  scope,
  onScopeChange,
  isStreaming
}) => {
  const [isScopeOpen, setIsScopeOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (sendBtnRef.current) magneticEffect(sendBtnRef.current);
  }, []);

  const scopes = [
    'Geral',
    'Espiritualidade e Retiros',
    'Social e Político',
    'Vida e Biografia',
    'Correspondência'
  ];

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-input-wrapper animate-slide-up">
      <div className="input-container">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Atribua uma pesquisa sobre o Magistério Dehoniano..."
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isStreaming}
        />
        <button
          ref={sendBtnRef}
          className={`send-btn ${isStreaming ? 'processing' : ''}`}
          onClick={onSend}
          disabled={!input.trim() || isStreaming}
          aria-label={isStreaming ? "Processando pesquisa" : "Enviar pesquisa"}
        >
          {isStreaming ? (
            <div className="btn-loader"></div>
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>

      <div className="input-footer">
        <div className="scope-selector">
          <button
            className="scope-btn"
            onClick={() => setIsScopeOpen(!isScopeOpen)}
            type="button"
            aria-haspopup="listbox"
            aria-expanded={isScopeOpen}
            aria-label={`Selecionar escopo de pesquisa. Escopo atual: ${scope}`}
          >
            <BookOpen size={14} />
            <span>Escopo: {scope}</span>
            <ChevronUp size={14} style={{ transform: isScopeOpen ? 'rotate(0)' : 'rotate(180deg)', transition: '0.2s' }} />
          </button>

          {isScopeOpen && (
            <div className="scope-dropdown">
              {scopes.map(s => (
                <div
                  key={s}
                  className={`scope-item ${scope === s ? 'selected' : ''}`}
                  onClick={() => {
                    onScopeChange(s);
                    setIsScopeOpen(false);
                  }}
                >
                  {s}
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="input-hint">Pressione Enter para pesquisar</div>
      </div>
    </div>
  );
};

export default ChatInput;
