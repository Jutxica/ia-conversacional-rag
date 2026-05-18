import React, { useState, useRef, useEffect } from 'react';
import './ChatInput.css';
import { Send } from 'lucide-react';
import { magneticEffect } from '../../utils/transitions';

interface ChatInputProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  isStreaming: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  input,
  onInputChange,
  onSend,
  isStreaming
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (sendBtnRef.current) magneticEffect(sendBtnRef.current);
  }, []);

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
        <div className="input-hint">Pressione Enter para pesquisar</div>
      </div>
    </div>
  );
};

export default ChatInput;
