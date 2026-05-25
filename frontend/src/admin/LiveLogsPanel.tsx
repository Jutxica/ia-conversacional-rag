import React, { useEffect, useState, useRef } from 'react';
import { Terminal, XCircle, AlertCircle, Info, CheckCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/chat', '') || 'http://localhost:8000';

interface LogMessage {
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: string;
}

interface Props {
  token: string;
}

export default function LiveLogsPanel({ token }: Props) {
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let retryTimeout: NodeJS.Timeout;
    
    const connect = () => {
      const url = `${API_BASE}/api/admin/logs/stream?token=${encodeURIComponent(token)}`;
      eventSource = new EventSource(url);
      
      eventSource.onopen = () => {
        setIsConnected(true);
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as LogMessage;
          setLogs(prev => [...prev, data].slice(-100)); // Keep last 100 logs
        } catch (e) {
          console.error("Failed to parse log", event.data);
        }
      };
      
      eventSource.onerror = (err) => {
        console.error("EventSource error", err);
        setIsConnected(false);
        if (eventSource) {
          eventSource.close();
        }
        // Try reconnecting after a delay
        retryTimeout = setTimeout(connect, 5000);
      };
    };
    
    connect();
    
    return () => {
      clearTimeout(retryTimeout);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [token]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'info': return <Info size={14} style={{ color: '#7ec8e0' }}/>;
      case 'success': return <CheckCircle size={14} style={{ color: '#3fb950' }}/>;
      case 'warning': return <AlertCircle size={14} style={{ color: '#d29922' }}/>;
      case 'error': return <XCircle size={14} style={{ color: '#ff6b6b' }}/>;
      default: return <Terminal size={14} style={{ color: '#8b949e' }}/>;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'info': return '#c9d1d9';
      case 'success': return '#3fb950';
      case 'warning': return '#d29922';
      case 'error': return '#ff6b6b';
      default: return '#c9d1d9';
    }
  };

  return (
    <div style={{
      background: '#0d1117',
      border: '1px solid #30363d',
      borderRadius: '8px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      height: '300px',
      marginTop: '24px'
    }}>
      <div style={{
        background: '#161b22',
        padding: '8px 16px',
        borderBottom: '1px solid #30363d',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={14} style={{ color: '#8b949e' }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#e6edf3' }}>Console de Ingestão (Tempo Real)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: isConnected ? '#3fb950' : '#ff6b6b'
          }} />
          <span style={{ fontSize: '11px', color: '#8b949e' }}>
            {isConnected ? 'Conectado' : 'Reconectando...'}
          </span>
        </div>
      </div>
      
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '12px',
        fontFamily: 'monospace',
        fontSize: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px'
      }}>
        {logs.length === 0 ? (
          <div style={{ color: '#484f58', fontStyle: 'italic' }}>Aguardando eventos do sistema...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
              <span style={{ color: '#8b949e', whiteSpace: 'nowrap' }}>
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              <div style={{ marginTop: '2px' }}>{getIcon(log.type)}</div>
              <span style={{ color: getColor(log.type), wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>{log.message}</span>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
