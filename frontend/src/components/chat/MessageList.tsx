import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './MessageList.css';
import { Book, BookOpen, Download, Copy, Check, User } from 'lucide-react';
import { magneticEffect } from '../../utils/transitions';
import type { UserProfile } from '../ui/ProfileModal';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
  metadata?: {
    confidence: { level: string; percentage: number };
    intent?: string;
  };
}

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  onViewCitations?: (messageId: string) => void;
  profile?: UserProfile;
  activeCitationMessageId?: string | null;
}

const preprocessMessageContent = (content: string, citations?: any[]) => {
  let processed = content;
  
  // 1. Destacar traduções colocando-as em itálico se estiverem entre parênteses
  // Exemplo: (Tradução livre: "...") -> _(Tradução livre: "...")_
  processed = processed.replace(/(?<!_)\(((?:tradu[çc]ã|traduz|trad\.|translation|traduzione)[^)]+)\)(?!_)/gi, '_($1)_');
  
  // 2. Tornar referências numéricas clicáveis
  // Exemplo: [1] -> [[1]](/api/pdfs/filename.pdf#page=20)
  if (citations && citations.length > 0) {
    processed = processed.replace(/\[(\d+)\]/g, (match, numStr) => {
      const idx = parseInt(numStr, 10) - 1;
      if (idx >= 0 && idx < citations.length) {
        const citation = citations[idx];
        const pageUrl = citation.page_url || '';
        if (pageUrl) {
          return `[\[${numStr}\]](${pageUrl})`;
        }
      }
      return match;
    });
  }
  
  return processed;
};

const handleCitationClick = (pageUrl: string) => {
  let targetUrl = pageUrl;
  if (!pageUrl.startsWith('http')) {
    const backendUrl = (import.meta.env.VITE_BACKEND_URL as string) || '';
    let base = '';
    if (backendUrl) {
      base = backendUrl.endsWith('/') ? backendUrl.slice(0, -1) : backendUrl;
    } else {
      const apiUrl = (import.meta.env.VITE_API_URL as string) || '';
      if (apiUrl && apiUrl.startsWith('http') && !apiUrl.includes('n8n.cloud')) {
        try {
          const urlObj = new URL(apiUrl);
          base = urlObj.origin;
        } catch (e) {
          console.error("Erro ao converter VITE_API_URL:", e);
        }
      }
      if (!base) {
        base = window.location.origin;
      }
    }
    targetUrl = `${base}${pageUrl}`;
  }
  window.open(targetUrl, '_blank');
};

const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  isStreaming, 
  onViewCitations,
  profile,
  activeCitationMessageId
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
    // Apply magnetic effect to all citation action buttons
    const buttons = document.querySelectorAll('.citation-action-btn');
    buttons.forEach(btn => magneticEffect(btn as HTMLElement));
  }, [messages, isStreaming]);

  return (
    <div className="message-list" ref={scrollRef}>
      {messages.map((m, idx) => (
        <div key={m.id} className={`message-row ${m.role} animate-fade-in`}>
          <div className="message-avatar-wrapper">
            {m.role === 'user' ? (
              <div className="avatar-circle user">
                {profile?.photoUrl ? (
                  <img src={profile.photoUrl} alt={profile?.name} className="avatar-img" />
                ) : (
                  profile?.name ? (
                    <span className="avatar-initials">{profile.name[0].toUpperCase()}</span>
                  ) : (
                    <User size={18} className="text-muted-foreground" />
                  )
                )}
              </div>
            ) : (
              <div className="avatar-circle assistant">
                <img src="/Avatar.png" alt="Dehon AI" className="avatar-img" />
              </div>
            )}
          </div>

          <div className="message-content-wrapper">
            <div className="message-header">
              <div className="sender-info">
                <span className="sender-name">
                  {m.role === 'user' ? (profile?.name || 'Pesquisador') : 'Padre Dehon'}
                </span>
                {m.role === 'assistant' && m.metadata && (
                  <div className="metadata-badges">
                    <span className={`confidence-badge ${m.metadata.confidence.level.toLowerCase()}`}>
                      Confiança {m.metadata.confidence.percentage}%
                    </span>
                    {m.metadata.intent && !['OCI_AGENT', 'AGENT', 'GENERAL', 'GERAL'].includes(m.metadata.intent.toUpperCase()) && (
                      <span className={`intent-badge ${m.metadata.intent.toLowerCase()}`}>
                        {m.metadata.intent}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                <button 
                  className={`header-citation-btn ${activeCitationMessageId === m.id ? 'active' : ''}`}
                  onClick={() => onViewCitations?.(m.id)}
                  title={activeCitationMessageId === m.id ? "Fechar referências" : "Abrir referências"}
                >
                  <BookOpen size={13} />
                  <span>Referências ({m.citations.length})</span>
                </button>
              )}
            </div>

            <div className={`message-bubble ${m.role}`}>
              {m.role === 'assistant' && m.content === '' && isStreaming && idx === messages.length - 1 ? (
                <div className="loader-wrapper">
                  <div className="loader"></div>
                  <div className="letter-wrapper">
                    {"Consultando o acervo...".split("").map((letter, i) => (
                      <span 
                        key={i} 
                        className="loader-letter"
                        style={{ animationDelay: `${i * 0.08}s` }}
                      >
                        {letter === " " ? "\u00A0" : letter}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div className={m.role === 'assistant' ? "prose dark:prose-invert prose-stone font-serif max-w-none text-[15px] prose-p:leading-relaxed prose-p:mb-4 last:prose-p:mb-0" : ""}>
                  {m.role === 'assistant' ? (
                    <ReactMarkdown
                      components={{
                        a: ({ href, children, ...props }) => {
                          const isPdf = href?.includes('/api/pdfs/');
                          if (isPdf) {
                            return (
                              <a
                                href={href}
                                onClick={(e) => {
                                  e.preventDefault();
                                  handleCitationClick(href!);
                                }}
                                className="inline-citation-badge"
                                title="Clique para abrir o PDF original nesta página"
                              >
                                {children}
                              </a>
                            );
                          }
                          return (
                            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                              {children}
                            </a>
                          );
                        },
                        em: ({ children, ...props }) => {
                          const textContent = React.Children.toArray(children).join('');
                          const isTranslation = /tradu[çc]ã|traduz|trad\.|translation|traduzione/i.test(textContent);
                          if (isTranslation) {
                            return (
                              <span className="translation-highlight" {...props}>
                                {children}
                              </span>
                            );
                          }
                          return <em {...props}>{children}</em>;
                        }
                      }}
                    >
                      {preprocessMessageContent(m.content, m.citations)}
                    </ReactMarkdown>
                  ) : (
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  )}
                </div>
              )}
              {isStreaming && m.content !== '' && idx === messages.length - 1 && (
                <span className="typing-cursor"></span>
              )}
            </div>

            {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
              <div className="sources-section">
                <div className="citation-actions-container">
                  <button 
                    className="citation-action-btn primary"
                    onClick={() => onViewCitations?.(m.id)}
                  >
                    <Book size={13} />
                    <span>Ver {m.citations.length} Referências</span>
                  </button>
                  <button 
                    className="citation-action-btn secondary"
                    onClick={() => {
                      if (showFormatted === m.id) {
                        setShowFormatted(null);
                      } else {
                        setShowFormatted(m.id);
                        handleExport(m.citations!);
                      }
                    }}
                  >
                    <Download size={13} />
                    <span>Exportar (.ris + ABNT)</span>
                  </button>
                </div>
                
                {showFormatted === m.id && (
                  <div className="abnt-format-box animate-fade-in">
                    <div className="abnt-header">
                      <strong className="abnt-title">Formatação ABNT</strong>
                      <button 
                        className={`abnt-copy-btn ${copied ? 'copied' : ''}`}
                        onClick={() => copyToClipboard(getABNT(m.citations!).replace(/\*\*/g, ''))}
                      >
                        {copied ? <Check size={13} /> : <Copy size={13} />}
                        <span>{copied ? 'Copiado!' : 'Copiar'}</span>
                      </button>
                    </div>
                    <div className="abnt-content">
                      {getABNT(m.citations!).split('\n\n').map((cite, i) => (
                        <p key={i}>
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
