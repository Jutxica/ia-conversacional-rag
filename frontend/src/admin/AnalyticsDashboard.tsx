import React, { useEffect, useState } from 'react';
import { BarChart3, Database, MessageSquare, Loader } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/chat', '') || 'http://localhost:8000';

interface AnalyticsData {
  total_documents: number;
  total_chats: number;
  cached_embeddings: number;
}

export default function AnalyticsDashboard({ token }: { token: string }) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/admin/analytics?token=${encodeURIComponent(token)}`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, [token]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <Loader className="animate-spin" size={24} color="#8b949e" />
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '16px' }}>
      <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '8px', padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ background: 'rgba(63, 185, 80, 0.1)', padding: '12px', borderRadius: '8px', color: '#3fb950' }}>
          <Database size={24} />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '24px', fontWeight: 600, color: '#e6edf3' }}>{data?.total_documents || 0}</h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#8b949e' }}>Fragmentos Indexados</p>
        </div>
      </div>

      <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '8px', padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ background: 'rgba(88, 166, 255, 0.1)', padding: '12px', borderRadius: '8px', color: '#58a6ff' }}>
          <MessageSquare size={24} />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '24px', fontWeight: 600, color: '#e6edf3' }}>{data?.total_chats || 0}</h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#8b949e' }}>Conversas Realizadas</p>
        </div>
      </div>

      <div style={{ background: '#0d1117', border: '1px solid #30363d', borderRadius: '8px', padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ background: 'rgba(210, 153, 34, 0.1)', padding: '12px', borderRadius: '8px', color: '#d29922' }}>
          <BarChart3 size={24} />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '24px', fontWeight: 600, color: '#e6edf3' }}>{data?.cached_embeddings || 0}</h3>
          <p style={{ margin: 0, fontSize: '13px', color: '#8b949e' }}>Consultas em Cache</p>
        </div>
      </div>
    </div>
  );
}
