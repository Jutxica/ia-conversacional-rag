import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './MessageList.css';
import { Book, Download, Copy, Check } from 'lucide-react';
import { magneticEffect } from '../../utils/transitions';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
  metadata?: {
    confidence: { level: string; percentage: number };
  };
}

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  session: any;
  onViewCitations?: (messageId: string) => void;
}

const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  isStreaming, 
  session,
  onViewCitations 
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showFormatted, setShowFormatted] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);

  const handleExport = (citations: any[]) => {
    // 1. Download RIS
    let ris = '';
    citations.forEach(c => {
      ris += `TY  - BOOK\n`;
      ris += `TI  - ${c.title || 'Referência Dehoniana'}\n`;
      if (c.author) ris += `AU  - ${c.author}\n`;
      const year = c.year || c.data || new Date().getFullYear();
      ris += `PY  - ${year}\n`;
      if (c.url) ris += `UR  - ${c.url}\n`;
      ris += `ER  - \n\n`;
    });
    const blob = new Blob([ris], { type: 'application/x-research-info-systems' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'referencias_dehon.ris';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getABNT = (citations: any[]) => {
    return citations.map(c => {
      const author = c.author ? c.author.toUpperCase() : 'DEHON, Leão';
      const year = c.year || c.data || 's.d.';
      const title = c.title ? `**${c.title}**` : '**Obra Dehoniana**';
      return `${author}. ${title}. ${year}.`;
    }).join('\n\n');
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
    // Apply magnetic effect to all view-citations buttons
    const buttons = document.querySelectorAll('.view-citations-btn');
    buttons.forEach(btn => magneticEffect(btn as HTMLElement));
  }, [messages, isStreaming]);

  return (
    <div className="message-list" ref={scrollRef}>
      {messages.map((m, idx) => (
        <div key={m.id} className={`message-row ${m.role} animate-fade-in`}>
          <div className="message-avatar-wrapper">
            {m.role === 'user' ? (
              <div className="avatar-circle user">
                {session?.user?.email?.[0].toUpperCase() || 'U'}
              </div>
            ) : (
              <div className="avatar-circle assistant">
                <img src="/Avatar.png" alt="Dehon AI" className="avatar-img" />
              </div>
            )}
          </div>

          <div className="message-content-wrapper">
            <div className="message-header">
              <span className="sender-name">
                {m.role === 'user' ? 'Pesquisador' : 'Padre Dehon'}
              </span>
              {m.role === 'assistant' && m.metadata && (
                <div className="metadata-badges">
                  <span className={`confidence-badge ${m.metadata.confidence.level.toLowerCase()}`}>
                    Confiança {m.metadata.confidence.percentage}%
                  </span>
                  {m.metadata.intent && (
                    <span className={`intent-badge ${m.metadata.intent.toLowerCase()}`}>
                      {m.metadata.intent}
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className={`message-bubble ${m.role}`}>
              {m.role === 'assistant' && m.content === '' && isStreaming && idx === messages.length - 1 ? (
                <div className="agentic-skeleton-wrapper">
                  <div className="shimmer-effect skeleton-line primary"></div>
                  <div className="shimmer-effect skeleton-line secondary"></div>
                  <div className="shimmer-effect skeleton-line tertiary"></div>
                  <span className="agent-status-text">Consultando o acervo dehoniano...</span>
                </div>
              ) : (
                <ReactMarkdown className={m.role === 'assistant' ? "prose dark:prose-invert prose-stone font-serif max-w-none text-[15px] prose-p:leading-relaxed prose-p:mb-4 last:prose-p:mb-0" : ""}>{m.content}</ReactMarkdown>
              )}
              {isStreaming && m.content !== '' && idx === messages.length - 1 && (
                <span className="typing-cursor"></span>
              )}
            </div>

            {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
              <div className="sources-section" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button 
                    className="view-citations-btn"
                    onClick={() => onViewCitations?.(m.id)}
                  >
                    <Book size={14} />
                    <span>Ver {m.citations.length} Referências</span>
                  </button>
                  <button 
                    className="view-citations-btn"
                    style={{ background: 'rgba(201, 169, 110, 0.1)', color: '#c9a96e', border: '1px solid rgba(201, 169, 110, 0.3)' }}
                    onClick={() => {
                      if (showFormatted === m.id) {
                        setShowFormatted(null);
                      } else {
                        setShowFormatted(m.id);
                        handleExport(m.citations!);
                      }
                    }}
                  >
                    <Download size={14} />
                    <span>Exportar (.ris + ABNT)</span>
                  </button>
                </div>
                
                {showFormatted === m.id && (
                  <div className="abnt-format-box animate-fade-in" style={{
                    marginTop: '8px', padding: '12px', background: '#0d1117', 
                    border: '1px solid #30363d', borderRadius: '6px', fontSize: '13px',
                    position: 'relative'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#8b949e' }}>
                      <strong style={{ color: '#e6edf3' }}>Formatação ABNT</strong>
                      <button onClick={() => copyToClipboard(getABNT(m.citations!).replace(/\*\*/g, ''))} style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', background: 'transparent', border: 'none', color: copied ? '#3fb950' : '#8b949e' }}>
                        {copied ? <Check size={14} /> : <Copy size={14} />}
                        {copied ? 'Copiado!' : 'Copiar'}
                      </button>
                    </div>
                    <div style={{ color: '#c9d1d9', lineHeight: '1.6' }}>
                      {getABNT(m.citations!).split('\n\n').map((cite, i) => (
                        <p key={i} style={{ marginBottom: '8px' }}>
                          <ReactMarkdown>{cite}</ReactMarkdown>
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
