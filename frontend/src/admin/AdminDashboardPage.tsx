import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Upload, FileText, Trash2, RefreshCw, CheckCircle, AlertTriangle, Loader, Database, LogOut, 
  Settings, BarChart3, Search, Plus, Edit2, X, Info, Calendar, ThumbsUp, ThumbsDown, 
  MessageSquare, HelpCircle, BookOpen, AlertCircle, Sun, Moon
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/chat', '') || 'http://localhost:8000';

interface DocItem {
  source_id: string;
  title: string;
  sigla: string;
  document_weight: number | string;
  chunks: number;
}

interface DocChunk {
  id: string;
  content: string;
  metadata: {
    source_id: string;
    title: string;
    sigla: string;
    chunk_index: number;
    [key: string]: any;
  };
}

interface SiglaItem {
  sigla: string;
  title: string;
  category: string;
  url_code: string;
  weight: number;
}

interface BlessedItem {
  id: string;
  question: string;
  answer: string;
  date: string;
}

interface LogItem {
  id: number;
  query: string;
  intent: string;
  num_citations: number;
  confidence_level: string;
  confidence_pct: number;
  conversation_id: string;
  created_at: string;
  feedback?: string | null;
  feedback_comment?: string | null;
}

interface MetricsData {
  total_chats: number;
  feedback: {
    positivo: number;
    negativo: number;
    rate: number;
  };
  intent_distribution: Record<string, number>;
  top_gaps: { term: string; count: number }[];
  using_fallback: boolean;
}

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

interface UploadState {
  status: UploadStatus;
  message: string;
  chunks?: number;
}

interface Props {
  token: string;
  onLogout: () => void;
  onBackToChat?: () => void;
}

type ActiveSection = 'metrics' | 'corpus' | 'upload' | 'url-ingest' | 'siglario' | 'blessed' | 'logs';

export default function AdminDashboardPage({ token, onLogout, onBackToChat }: Props) {
  const [activeSection, setActiveSection] = useState<ActiveSection>('metrics');
  const [theme, setTheme] = useState<'light' | 'midnight'>((localStorage.getItem('dehon-theme') as any) || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    const newTheme = theme === 'midnight' ? 'light' : 'midnight';
    setTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('dehon-theme', newTheme);
  };
  
  // Corpus State
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  // Chunks Modal State
  const [selectedDoc, setSelectedDoc] = useState<DocItem | null>(null);
  const [docChunks, setDocChunks] = useState<DocChunk[]>([]);
  const [isLoadingChunks, setIsLoadingChunks] = useState(false);
  const [isChunksModalOpen, setIsChunksModalOpen] = useState(false);
  
  // Upload State
  const [isDragging, setIsDragging] = useState(false);
  const [upload, setUpload] = useState<UploadState>({ status: 'idle', message: '' });
  const [sigla, setSigla] = useState('PDF');
  const [docTitle, setDocTitle] = useState('');
  const [weight, setWeight] = useState(5);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Siglário State
  const [siglarioList, setSiglarioList] = useState<SiglaItem[]>([]);
  const [isLoadingSiglario, setIsLoadingSiglario] = useState(false);
  const [isSiglarioModalOpen, setIsSiglarioModalOpen] = useState(false);
  const [editingSigla, setEditingSigla] = useState<SiglaItem | null>(null);
  const [newSigla, setNewSigla] = useState<SiglaItem>({ sigla: '', title: '', category: 'Obras Espirituais', url_code: '', weight: 5 });
  const [corpusFilterCategory, setCorpusFilterCategory] = useState<string>('Todas');
  const [siglarioFilterCategory, setSiglarioFilterCategory] = useState<string>('Todas');
  const CATEGORIES = ['Todas', 'Obras Espirituais', 'Obras Sociais', 'Diários', 'Viagens', 'Outros'];
  
  // Blessed State
  const [blessedList, setBlessedList] = useState<BlessedItem[]>([]);
  const [isLoadingBlessed, setIsLoadingBlessed] = useState(false);
  const [isBlessedModalOpen, setIsBlessedModalOpen] = useState(false);
  const [editingBlessed, setEditingBlessed] = useState<BlessedItem | null>(null);
  const [newBlessed, setNewBlessed] = useState<{ question: string; answer: string }>({ question: '', answer: '' });
  const [searchBlessedQuery, setSearchBlessedQuery] = useState('');
  
  // Logs State
  const [logsList, setLogsList] = useState<LogItem[]>([]);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);
  const [usingFallbackLogs, setUsingFallbackLogs] = useState(false);
  const [searchLogQuery, setSearchLogQuery] = useState('');
  
  // Metrics State
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);

  // URL Ingest State
  const [urlIngestUrl, setUrlIngestUrl] = useState('');
  const [urlIngestTitle, setUrlIngestTitle] = useState('');
  const [urlIngestSigla, setUrlIngestSigla] = useState('WEB');
  const [urlIngestWeight, setUrlIngestWeight] = useState(5);
  const [urlIngest, setUrlIngest] = useState<UploadState>({ status: 'idle', message: '' });

  const authHeaders = { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  // --- API Fetches ---
  
  const fetchDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents`, { 
        headers: { 'Authorization': `Bearer ${token}` } 
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (e: any) {
      console.error('Erro ao buscar documentos:', e);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const fetchDocumentChunks = async (doc: DocItem) => {
    setSelectedDoc(doc);
    setIsLoadingChunks(true);
    setIsChunksModalOpen(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents/${encodeURIComponent(doc.source_id)}/chunks`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDocChunks(data.chunks || []);
    } catch (e: any) {
      console.error('Erro ao buscar chunks:', e);
      setDocChunks([]);
    } finally {
      setIsLoadingChunks(false);
    }
  };

  const handleDeleteDoc = async (sourceId: string) => {
    if (!confirm(`Remover permanentemente todos os fragmentos de "${sourceId}" do corpus?`)) return;
    setDeletingId(sourceId);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents/${encodeURIComponent(sourceId)}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      const data = await res.json();
      if (res.ok) {
        setDocuments(prev => prev.filter(d => d.source_id !== sourceId));
        setTotalChunks(prev => prev - (data.chunks_deleted || 0));
        fetchMetrics(); // Refresh metrics
      }
    } catch (e) {
      console.error('Erro ao deletar documento:', e);
    } finally {
      setDeletingId(null);
    }
  };

  const fetchSiglario = async () => {
    setIsLoadingSiglario(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/siglario`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const works = data.works || {};
      const list = Object.entries(works).map(([siglaKey, val]: [string, any]) => ({
        sigla: siglaKey,
        title: val.title || '',
        category: val.category || '',
        url_code: val.url_code || '',
        weight: val.weight || 5
      }));
      setSiglarioList(list);
    } catch (e) {
      console.error('Erro ao buscar siglário:', e);
    } finally {
      setIsLoadingSiglario(false);
    }
  };

  const handleSaveSiglario = async (e: React.FormEvent) => {
    e.preventDefault();
    const item = editingSigla || newSigla;
    if (!item.sigla.trim()) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/admin/siglario`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(item)
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (res.ok) {
        setIsSiglarioModalOpen(false);
        setEditingSigla(null);
        setNewSigla({ sigla: '', title: '', category: 'Obras Espirituais', url_code: '', weight: 5 });
        fetchSiglario();
      }
    } catch (e) {
      console.error('Erro ao salvar sigla:', e);
    }
  };

  const handleDeleteSiglario = async (siglaKey: string) => {
    if (!confirm(`Remover "${siglaKey}" do siglário? Isso não altera os PDFs do corpus, mas remove a referência.`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/admin/siglario/${encodeURIComponent(siglaKey)}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (res.ok) {
        fetchSiglario();
      }
    } catch (e) {
      console.error('Erro ao deletar sigla:', e);
    }
  };

  const fetchBlessed = async () => {
    setIsLoadingBlessed(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/blessed`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setBlessedList(data.answers || []);
    } catch (e) {
      console.error('Erro ao buscar blessed answers:', e);
    } finally {
      setIsLoadingBlessed(false);
    }
  };

  const handleSaveBlessed = async (e: React.FormEvent) => {
    e.preventDefault();
    const isEdit = !!editingBlessed;
    const bodyData = isEdit ? editingBlessed : newBlessed;
    
    if (!bodyData?.question?.trim() || !bodyData?.answer?.trim()) return;

    try {
      const url = isEdit 
        ? `${API_BASE}/api/admin/blessed/${editingBlessed.id}`
        : `${API_BASE}/api/admin/blessed`;
      const method = isEdit ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: authHeaders,
        body: JSON.stringify(bodyData)
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (res.ok) {
        setIsBlessedModalOpen(false);
        setEditingBlessed(null);
        setNewBlessed({ question: '', answer: '' });
        fetchBlessed();
      }
    } catch (e) {
      console.error('Erro ao salvar blessed answer:', e);
    }
  };

  const handleDeleteBlessed = async (id: string) => {
    if (!confirm('Excluir esta resposta validada?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/admin/blessed/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (res.ok) {
        fetchBlessed();
      }
    } catch (e) {
      console.error('Erro ao deletar blessed answer:', e);
    }
  };

  const fetchLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/logs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setLogsList(data.logs || []);
      setUsingFallbackLogs(!!data.using_fallback);
    } catch (e) {
      console.error('Erro ao buscar logs:', e);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const fetchMetrics = async () => {
    setIsLoadingMetrics(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/metrics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      console.error('Erro ao buscar métricas:', e);
    } finally {
      setIsLoadingMetrics(false);
    }
  };

  // --- Initial Load & Tab switching ---
  useEffect(() => {
    if (activeSection === 'metrics') fetchMetrics();
    else if (activeSection === 'corpus') {
      fetchDocuments();
      if (siglarioList.length === 0) fetchSiglario();
    }
    else if (activeSection === 'siglario') fetchSiglario();
    else if (activeSection === 'blessed') fetchBlessed();
    else if (activeSection === 'logs') fetchLogs();
  }, [activeSection]);

  const handleRefresh = () => {
    if (activeSection === 'metrics') fetchMetrics();
    else if (activeSection === 'corpus') fetchDocuments();
    else if (activeSection === 'siglario') fetchSiglario();
    else if (activeSection === 'blessed') fetchBlessed();
    else if (activeSection === 'logs') fetchLogs();
  };

  // --- Document Upload ---
  const handleUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUpload({ status: 'error', message: 'Apenas arquivos PDF são aceitos.' });
      return;
    }

    setUpload({ status: 'uploading', message: `Extraindo textos e vetorizando "${file.name}"...` });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('sigla', sigla);
    formData.append('document_weight', String(weight));
    if (docTitle.trim()) formData.append('title', docTitle.trim());

    try {
      const res = await fetch(`${API_BASE}/api/admin/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      const data = await res.json();

      if (!res.ok) {
        setUpload({ status: 'error', message: data.detail || 'Erro ao processar PDF no servidor.' });
        return;
      }

      setUpload({
        status: 'success',
        message: `"${data.document}" indexado com sucesso!`,
        chunks: data.chunks_inserted,
      });
      setDocTitle('');
      setSigla('PDF');
      setWeight(5);
    } catch (e: any) {
      setUpload({ status: 'error', message: `Erro de conexão: ${e.message}` });
    }
  };

  const handleUrlIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlIngestUrl.trim()) return;

    const urls = urlIngestUrl.trim().split('\n').map(u => u.trim()).filter(u => u);
    if (urls.length === 0) return;

    let totalChunks = 0;
    let successCount = 0;

    for (let i = 0; i < urls.length; i++) {
      const currentUrl = urls[i];
      setUrlIngest({ status: 'uploading', message: `Raspando e indexando URL ${i + 1} de ${urls.length}:\n${currentUrl}...` });

      try {
        const res = await fetch(`${API_BASE}/api/admin/ingest-url`, {
          method: 'POST',
          headers: authHeaders,
          body: JSON.stringify({
            url: currentUrl,
            title: urls.length === 1 ? (urlIngestTitle.trim() || undefined) : undefined,
            sigla: urlIngestSigla,
            document_weight: urlIngestWeight,
          }),
        });

        if (res.status === 401 || res.status === 403) { onLogout(); return; }
        const data = await res.json();

        if (res.ok) {
          successCount++;
          totalChunks += (data.chunks_inserted || 0);
        } else {
          console.error(`Erro ao indexar ${currentUrl}:`, data.detail);
        }
      } catch (err: any) {
         console.error(`Erro na requisição para ${currentUrl}:`, err.message);
      }
    }

    if (successCount > 0) {
      setUrlIngest({
        status: 'success',
        message: `${successCount} URL(s) indexada(s) com sucesso! Total de fragmentos gerados: ${totalChunks}`,
        chunks: totalChunks,
      });
      setUrlIngestUrl('');
      setUrlIngestTitle('');
      setUrlIngestSigla('WEB');
      setUrlIngestWeight(5);
    } else {
      setUrlIngest({
        status: 'error',
        message: 'Nenhuma URL pôde ser processada com sucesso. Verifique o console para detalhes.',
      });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = '';
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  }, [sigla, docTitle, weight, token]);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  // --- Helpers ---
  const weightColor = (w: number | string) => {
    const n = Number(w);
    if (n >= 8) return '#c9a96e'; // Ouro
    if (n >= 5) return '#7ec8e0'; // Azul claro
    return '#8b9bb4'; // Cinza azulado
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('pt-BR');
    } catch {
      return dateStr;
    }
  };

  // --- Filtered lists ---
  const getDocCategory = (sigla: string) => {
    if (!sigla) return 'Outros';
    const cleanSigla = sigla.trim().toUpperCase();
    const siglaInfo = siglarioList.find(s => s.sigla?.trim().toUpperCase() === cleanSigla);
    return siglaInfo ? siglaInfo.category : 'Outros';
  };

  const filteredDocuments = documents.filter(doc => {
    if (corpusFilterCategory === 'Todas') return true;
    const docCat = getDocCategory(doc.sigla).trim().toLowerCase();
    return docCat === corpusFilterCategory.trim().toLowerCase();
  });

  const filteredSiglario = siglarioList.filter(item => {
    if (siglarioFilterCategory === 'Todas') return true;
    const itemCat = (item.category || 'Outros').trim().toLowerCase();
    return itemCat === siglarioFilterCategory.trim().toLowerCase();
  });

  const filteredBlessed = blessedList.filter(item => 
    item.question.toLowerCase().includes(searchBlessedQuery.toLowerCase()) || 
    item.answer.toLowerCase().includes(searchBlessedQuery.toLowerCase())
  );

  const filteredLogs = logsList.filter(item => 
    item.query.toLowerCase().includes(searchLogQuery.toLowerCase()) ||
    (item.feedback_comment && item.feedback_comment.toLowerCase().includes(searchLogQuery.toLowerCase()))
  );

  return (
    <div className="adm-root">
      {/* Sidebar */}
      <aside className="adm-sidebar">
        <div className="adm-sidebar-brand">
          <div className="adm-brand-logo">D</div>
          <div>
            <div className="adm-brand-name">Dehon AI</div>
            <div className="adm-brand-sub">Painel Admin</div>
          </div>
        </div>

        <nav className="adm-nav">
          <button
            className={`adm-nav-item ${activeSection === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveSection('metrics')}
          >
            <BarChart3 size={16} />
            <span>Métricas</span>
          </button>
          
          <button
            className={`adm-nav-item ${activeSection === 'corpus' ? 'active' : ''}`}
            onClick={() => setActiveSection('corpus')}
          >
            <Database size={16} />
            <span>Corpus Dehoniano</span>
          </button>
          
          <button
            className={`adm-nav-item ${activeSection === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveSection('upload')}
          >
            <Upload size={16} />
            <span>Ingestão de PDF</span>
          </button>

          <button
            className={`adm-nav-item ${activeSection === 'url-ingest' ? 'active' : ''}`}
            onClick={() => setActiveSection('url-ingest')}
          >
            <Search size={16} />
            <span>Ingestão via URL</span>
          </button>
          
          <button
            className={`adm-nav-item ${activeSection === 'siglario' ? 'active' : ''}`}
            onClick={() => setActiveSection('siglario')}
          >
            <BookOpen size={16} />
            <span>Siglário</span>
          </button>

          <button
            className={`adm-nav-item ${activeSection === 'blessed' ? 'active' : ''}`}
            onClick={() => setActiveSection('blessed')}
          >
            <HelpCircle size={16} />
            <span>Blessed Answers</span>
          </button>

          <button
            className={`adm-nav-item ${activeSection === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveSection('logs')}
          >
            <MessageSquare size={16} />
            <span>Logs de Busca</span>
          </button>
        </nav>

        <div className="adm-sidebar-footer" style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '4px', padding: '12px 16px', borderTop: '1px solid var(--adm-border)' }}>
          {onBackToChat && (
            <button className="adm-nav-item adm-nav-item-footer" onClick={onBackToChat} style={{ border: 'none', background: 'transparent', margin: 0, width: '100%' }}>
              <Info size={16} />
              <span>Voltar ao Chat</span>
            </button>
          )}

          <button className="adm-nav-item adm-nav-item-footer" onClick={toggleTheme} style={{ border: 'none', background: 'transparent', margin: 0, width: '100%' }}>
            {theme === 'midnight' ? <Sun size={16} /> : <Moon size={16} />}
            <span>{theme === 'midnight' ? 'Modo Claro' : 'Modo Escuro'}</span>
          </button>

          <button className="adm-logout" onClick={onLogout} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', background: 'transparent', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '13px', transition: 'background 0.15s, color 0.15s' }}>
            <LogOut size={15} />
            <span>Sair da Conta</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="adm-main">
        {/* Top Bar */}
        <div className="adm-topbar">
          <div className="adm-topbar-left">
            <h1 className="adm-page-title">
              {activeSection === 'metrics' && 'Painel Geral e Métricas'}
              {activeSection === 'corpus' && 'Corpus Dehoniano'}
              {activeSection === 'upload' && 'Ingestão de Novos Documentos'}
              {activeSection === 'url-ingest' && 'Ingestão via URL (Firecrawl)'}
              {activeSection === 'siglario' && 'Dicionário de Siglas (Siglário)'}
              {activeSection === 'blessed' && 'Respostas Curadas (Blessed Answers)'}
              {activeSection === 'logs' && 'Logs de Auditoria e Feedback'}
            </h1>
            <p className="adm-page-desc">
              {activeSection === 'metrics' && 'Visão consolidada da operação, satisfação dos pesquisadores e lacunas detectadas.'}
              {activeSection === 'corpus' && 'Gerencie os livros, diários e cartas indexados na base RAG.'}
              {activeSection === 'upload' && 'Faça o upload de documentos PDF. Os textos serão processados via Firecrawl e vetorizados.'}
              {activeSection === 'url-ingest' && 'Raspe uma página web e ingira seu conteúdo no corpus RAG automaticamente via Firecrawl.'}
              {activeSection === 'siglario' && 'Abreviações e siglas das obras do Padre Dehon usadas na expansão de busca.'}
              {activeSection === 'blessed' && 'Respostas de especialistas injetadas no contexto RAG para perguntas críticas.'}
              {activeSection === 'logs' && 'Histórico de perguntas, intenções, scores de confiança e avaliações dos usuários.'}
            </p>
          </div>
          
          {activeSection !== 'upload' && activeSection !== 'url-ingest' && (

            <button
              className="adm-refresh-btn"
              onClick={handleRefresh}
              title="Atualizar dados"
            >
              <RefreshCw size={15} className={
                isLoadingDocs || isLoadingSiglario || isLoadingBlessed || isLoadingLogs || isLoadingMetrics 
                  ? 'spinning' 
                  : ''
              } />
            </button>
          )}
        </div>

        {/* --- SECTION: METRICS --- */}
        {activeSection === 'metrics' && (
          <div className="adm-content">
            {isLoadingMetrics ? (
              <div className="adm-empty-state">
                <Loader size={30} className="spinning adm-gold" />
                <p>Carregando análises de métricas...</p>
              </div>
            ) : metrics ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                
                {/* Fallback Warning if supabase search_logs fails */}
                {metrics.using_fallback && (
                  <div className="adm-feedback adm-feedback--error" style={{ marginTop: 0, borderStyle: 'dashed' }}>
                    <AlertCircle size={16} />
                    <span>
                      <strong>Banco de Dados (search_logs) indisponível:</strong> Mostrando dados acumulados a partir do log de fallback local.
                    </span>
                  </div>
                )}

                <div className="adm-stats-row">
                  <div className="adm-stat-card">
                    <span className="adm-stat-num">{metrics.total_chats}</span>
                    <span className="adm-stat-lbl">Consultas Realizadas</span>
                  </div>
                  <div className="adm-stat-card">
                    <span className="adm-stat-num" style={{ color: '#3fb950' }}>
                      {metrics.feedback.rate}%
                    </span>
                    <span className="adm-stat-lbl">Aprovação do Usuário</span>
                  </div>
                  <div className="adm-stat-card">
                    <span className="adm-stat-num" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <span style={{ color: '#3fb950', fontSize: '18px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <ThumbsUp size={16} /> {metrics.feedback.positivo}
                      </span>
                      <span style={{ color: '#ff6b6b', fontSize: '18px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <ThumbsDown size={16} /> {metrics.feedback.negativo}
                      </span>
                    </span>
                    <span className="adm-stat-lbl">Feedbacks Recebidos</span>
                  </div>
                </div>

                <div className="adm-grid-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  {/* Intent Distribution */}
                  <div className="adm-card" style={{ background: '#161b22', border: '1px solid #21262d', borderRadius: '12px', padding: '24px' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f0f6fc', marginBottom: '16px', borderBottom: '1px solid #21262d', paddingBottom: '12px' }}>
                      Distribuição de Intenções de Busca
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {Object.entries(metrics.intent_distribution).length === 0 ? (
                        <p style={{ color: '#8b949e', fontSize: '13px' }}>Nenhum log encontrado para classificar intenções.</p>
                      ) : (
                        Object.entries(metrics.intent_distribution)
                          .sort((a, b) => b[1] - a[1])
                          .map(([intent, count]) => {
                            const pct = metrics.total_chats > 0 ? (count / metrics.total_chats) * 100 : 0;
                            return (
                              <div key={intent} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                  <span style={{ fontFamily: 'monospace', color: '#c9a96e' }}>{intent}</span>
                                  <span style={{ color: '#8b949e' }}>{count} ({pct.toFixed(0)}%)</span>
                                </div>
                                <div style={{ background: '#21262d', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                                  <div style={{ background: '#c9a96e', width: `${pct}%`, height: '100%' }} />
                                </div>
                              </div>
                            );
                          })
                      )}
                    </div>
                  </div>

                  {/* Knowledge Gaps */}
                  <div className="adm-card" style={{ background: '#161b22', border: '1px solid #21262d', borderRadius: '12px', padding: '24px' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f0f6fc', marginBottom: '16px', borderBottom: '1px solid #21262d', paddingBottom: '12px' }}>
                      Lacunas de Conhecimento RAG (Top Termos com Baixa Confiança)
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      {metrics.top_gaps.length === 0 ? (
                        <p style={{ color: '#8b949e', fontSize: '13px' }}>Nenhuma lacuna detectada (confiança sempre média/alta).</p>
                      ) : (
                        metrics.top_gaps.map((gap, idx) => (
                          <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#0d1117', borderRadius: '8px', border: '1px dashed #30363d' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <span style={{ fontSize: '13px', fontWeight: 500, color: '#e6edf3' }}>"{gap.term}"</span>
                              <span style={{ fontSize: '11px', color: '#8b949e' }}>Classificado como Confiança Baixa</span>
                            </div>
                            <span style={{ background: 'rgba(255, 107, 107, 0.15)', color: '#ff6b6b', fontSize: '11px', fontWeight: 600, padding: '3px 8px', borderRadius: '4px' }}>
                              {gap.count}x ocorrencias
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

              </div>
            ) : (
              <div className="adm-empty-state">
                <AlertTriangle size={32} />
                <p>Nenhum dado de métrica disponível.</p>
              </div>
            )}
          </div>
        )}

        {/* --- SECTION: CORPUS --- */}
        {activeSection === 'corpus' && (
          <div className="adm-content">
            <div className="adm-stats-row">
              <div className="adm-stat-card">
                <span className="adm-stat-num">{documents.length}</span>
                <span className="adm-stat-lbl">Documentos Únicos</span>
              </div>
              <div className="adm-stat-card">
                <span className="adm-stat-num">{totalChunks.toLocaleString('pt-BR')}</span>
                <span className="adm-stat-lbl">Fragmentos Ativos</span>
              </div>
              <div className="adm-stat-card adm-stat-card--action" onClick={() => setActiveSection('upload')}>
                <Plus size={20} style={{ color: '#c9a96e' }} />
                <span className="adm-stat-lbl" style={{ color: '#c9a96e', fontWeight: 600 }}>Registrar PDF</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', marginTop: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '13px', color: 'var(--adm-text-secondary)', fontWeight: 500 }}>Filtrar por Escopo:</span>
                <select 
                  className="adm-input" 
                  style={{ width: '200px', padding: '6px 10px' }}
                  value={corpusFilterCategory}
                  onChange={e => setCorpusFilterCategory(e.target.value)}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            <div className="adm-table-wrap">
              {isLoadingDocs && documents.length === 0 ? (
                <div className="adm-empty-state">
                  <Loader size={24} className="spinning" />
                  <p>Acessando base vetorial...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="adm-empty-state">
                  <FileText size={40} style={{ opacity: 0.3 }} />
                  <p>A base de documentos está vazia.</p>
                  <button className="adm-cta-btn" onClick={() => setActiveSection('upload')}>
                    Indexar Primeiro Livro
                  </button>
                </div>
              ) : (
                <table className="adm-table">
                  <thead>
                    <tr>
                      <th>Documento</th>
                      <th>Sigla</th>
                      <th>Fragmentos (Chunks)</th>
                      <th>Peso Semântico</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDocuments.map(doc => (
                      <tr key={doc.source_id}>
                        <td>
                          <div className="adm-doc-cell">
                            <FileText size={14} className="adm-doc-icon" />
                            <span 
                              className="adm-doc-title" 
                              style={{ cursor: 'pointer', textDecoration: 'underline' }}
                              onClick={() => fetchDocumentChunks(doc)}
                              title="Visualizar fragmentos indexados"
                            >
                              {doc.title || doc.source_id}
                            </span>
                          </div>
                        </td>
                        <td><span className="adm-badge">{doc.sigla}</span></td>
                        <td className="adm-num-cell">{doc.chunks.toLocaleString('pt-BR')}</td>
                        <td>
                          <span className="adm-weight" style={{ color: weightColor(doc.document_weight) }}>
                            {doc.document_weight}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              className="adm-delete-btn"
                              style={{ color: '#7ec8e0', borderColor: 'transparent' }}
                              onClick={() => fetchDocumentChunks(doc)}
                              title="Ver Detalhes do Conteúdo"
                            >
                              <Info size={13} />
                            </button>
                            <button
                              className="adm-delete-btn"
                              onClick={() => handleDeleteDoc(doc.source_id)}
                              disabled={deletingId === doc.source_id}
                              title="Deletar da Base RAG"
                            >
                              {deletingId === doc.source_id
                                ? <Loader size={13} className="spinning" />
                                : <Trash2 size={13} />
                              }
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* --- SECTION: UPLOAD --- */}
        {activeSection === 'upload' && (
          <div className="adm-content">
            <div className="adm-upload-wrap">
              <div className="adm-meta-grid">
                <div className="adm-meta-field">
                  <label>Título do documento</label>
                  <input
                    type="text"
                    placeholder="Ex: Diário do Padre Dehon - Vol II"
                    value={docTitle}
                    onChange={e => setDocTitle(e.target.value)}
                    className="adm-input"
                  />
                </div>
                <div className="adm-meta-field adm-meta-field--sm">
                  <label>Sigla da Obra</label>
                  <input
                    type="text"
                    placeholder="Ex: DSP"
                    value={sigla}
                    maxLength={10}
                    onChange={e => setSigla(e.target.value.toUpperCase())}
                    className="adm-input"
                  />
                </div>
                <div className="adm-meta-field adm-meta-field--sm">
                  <label>Peso Semântico ({weight})</label>
                  <input
                    type="range"
                    min={1}
                    max={10}
                    value={weight}
                    onChange={e => setWeight(Number(e.target.value))}
                    className="adm-range"
                  />
                </div>
              </div>

              <div
                className={`adm-dropzone ${isDragging ? 'dragging' : ''} ${upload.status === 'uploading' ? 'uploading' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => upload.status !== 'uploading' && fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                {upload.status === 'uploading' ? (
                  <div className="adm-dz-content">
                    <Loader size={32} className="spinning adm-gold" />
                    <p className="adm-dz-title">{upload.message}</p>
                    <span className="adm-dz-hint">Firecrawl está processando as páginas e inserindo os vetores...</span>
                    <div className="adm-progress-bar">
                      <div className="adm-progress-fill" />
                    </div>
                  </div>
                ) : (
                  <div className="adm-dz-content">
                    <Upload size={32} className="adm-dz-icon" />
                    <p className="adm-dz-title">Arraste o arquivo PDF aqui ou clique para selecionar</p>
                    <span className="adm-dz-hint">Até 100MB · Ingestão otimizada com extração estruturada</span>
                  </div>
                )}
              </div>

              {upload.status === 'success' && (
                <div className="adm-feedback adm-feedback--success">
                  <CheckCircle size={16} />
                  <span>{upload.message}</span>
                  {upload.chunks !== undefined && (
                    <span className="adm-feedback-detail">· {upload.chunks.toLocaleString('pt-BR')} fragmentos criados na base vetorial.</span>
                  )}
                  <button onClick={() => setUpload({ status: 'idle', message: '' })} className="adm-feedback-close">✕</button>
                </div>
              )}
              
              {upload.status === 'error' && (
                <div className="adm-feedback adm-feedback--error">
                  <AlertTriangle size={16} />
                  <span>{upload.message}</span>
                  <button onClick={() => setUpload({ status: 'idle', message: '' })} className="adm-feedback-close">✕</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- SECTION: URL INGEST --- */}
        {activeSection === 'url-ingest' && (
          <div className="adm-content">
            <div className="adm-upload-wrap">
              <form onSubmit={handleUrlIngest}>
                <div style={{ marginBottom: '20px' }}>
                  <div className="adm-meta-field" style={{ marginBottom: '16px' }}>
                    <label>URL da página web (ou múltiplas URLs, uma por linha)</label>
                    <textarea
                      placeholder="https://dehon.ieme.it/pt/obras/...&#10;https://dehon.ieme.it/pt/cartas/..."
                      value={urlIngestUrl}
                      onChange={e => setUrlIngestUrl(e.target.value)}
                      className="adm-input"
                      rows={5}
                      required
                      disabled={urlIngest.status === 'uploading'}
                      style={{ resize: 'vertical' }}
                    />
                  </div>
                  <div className="adm-meta-grid">
                    <div className="adm-meta-field">
                      <label>Título (opcional)</label>
                      <input
                        type="text"
                        placeholder="Ex: Carta a los Escolásticos - 1892"
                        value={urlIngestTitle}
                        onChange={e => setUrlIngestTitle(e.target.value)}
                        className="adm-input"
                        disabled={urlIngest.status === 'uploading'}
                      />
                    </div>
                    <div className="adm-meta-field adm-meta-field--sm">
                      <label>Sigla da Obra</label>
                      <input
                        type="text"
                        placeholder="Ex: WEB"
                        value={urlIngestSigla}
                        maxLength={10}
                        onChange={e => setUrlIngestSigla(e.target.value.toUpperCase())}
                        className="adm-input"
                        disabled={urlIngest.status === 'uploading'}
                      />
                    </div>
                    <div className="adm-meta-field adm-meta-field--sm">
                      <label>Peso Semântico ({urlIngestWeight})</label>
                      <input
                        type="range"
                        min={1}
                        max={10}
                        value={urlIngestWeight}
                        onChange={e => setUrlIngestWeight(Number(e.target.value))}
                        className="adm-range"
                        disabled={urlIngest.status === 'uploading'}
                      />
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  className="adm-cta-btn"
                  disabled={urlIngest.status === 'uploading' || !urlIngestUrl.trim()}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '200px' }}
                >
                  {urlIngest.status === 'uploading' ? (
                    <>
                      <Loader size={15} className="spinning" />
                      Processando URL...
                    </>
                  ) : (
                    <>
                      <Search size={15} />
                      Raspar e Indexar URL
                    </>
                  )}
                </button>
              </form>

              {urlIngest.status === 'uploading' && (
                <div style={{ marginTop: '20px' }}>
                  <div className="adm-progress-bar" style={{ width: '100%' }}>
                    <div className="adm-progress-fill" />
                  </div>
                  <p style={{ fontSize: '12px', color: '#8b949e', marginTop: '8px' }}>{urlIngest.message}</p>
                </div>
              )}

              {urlIngest.status === 'success' && (
                <div className="adm-feedback adm-feedback--success" style={{ marginTop: '20px' }}>
                  <CheckCircle size={16} />
                  <span>{urlIngest.message}</span>
                  {urlIngest.chunks !== undefined && (
                    <span className="adm-feedback-detail">· {urlIngest.chunks.toLocaleString('pt-BR')} fragmentos criados na base vetorial.</span>
                  )}
                  <button onClick={() => setUrlIngest({ status: 'idle', message: '' })} className="adm-feedback-close">✕</button>
                </div>
              )}

              {urlIngest.status === 'error' && (
                <div className="adm-feedback adm-feedback--error" style={{ marginTop: '20px' }}>
                  <AlertTriangle size={16} />
                  <span>{urlIngest.message}</span>
                  <button onClick={() => setUrlIngest({ status: 'idle', message: '' })} className="adm-feedback-close">✕</button>
                </div>
              )}

              <div style={{ marginTop: '28px', padding: '16px', background: 'rgba(201,169,110,0.06)', border: '1px solid rgba(201,169,110,0.18)', borderRadius: '10px' }}>
                <p style={{ fontSize: '12px', color: '#c9a96e', fontWeight: 600, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Info size={13} /> Sobre a Ingestão via URL
                </p>
                <ul style={{ fontSize: '12px', color: '#8b949e', lineHeight: '1.7', listStyleType: 'disc', paddingLeft: '16px' }}>
                  <li>O Firecrawl raspa o conteúdo principal da página (ignora menus e rodapés).</li>
                  <li>O texto é normalizado, dividido em chunks de até 800 tokens com overlap de 150 tokens.</li>
                  <li>Cada chunk recebe um embedding 2000-dim e é indexado na tabela <code>documents</code> no Supabase.</li>
                  <li>O campo <strong>source_url</strong> é salvo nos metadados para rastreabilidade.</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* --- SECTION: SIGLARIO --- */}
        {activeSection === 'siglario' && (
          <div className="adm-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '13px', color: 'var(--adm-text-secondary)', fontWeight: 500 }}>Filtrar por Escopo:</span>
                <select 
                  className="adm-input" 
                  style={{ width: '200px', padding: '6px 10px' }}
                  value={siglarioFilterCategory}
                  onChange={e => setSiglarioFilterCategory(e.target.value)}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <button 
                className="adm-cta-btn" 
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                onClick={() => {
                  setEditingSigla(null);
                  setNewSigla({ sigla: '', title: '', category: 'Obras Espirituais', url_code: '', weight: 5 });
                  setIsSiglarioModalOpen(true);
                }}
              >
                <Plus size={14} /> Nova Sigla
              </button>
            </div>

            <div className="adm-table-wrap">
              {isLoadingSiglario && siglarioList.length === 0 ? (
                <div className="adm-empty-state">
                  <Loader size={24} className="spinning" />
                  <p>Acessando dicionário...</p>
                </div>
              ) : siglarioList.length === 0 ? (
                <div className="adm-empty-state">
                  <BookOpen size={40} style={{ opacity: 0.3 }} />
                  <p>Nenhuma sigla cadastrada.</p>
                </div>
              ) : (
                <table className="adm-table">
                  <thead>
                    <tr>
                      <th>Sigla</th>
                      <th>Título Descritivo</th>
                      <th>Categoria</th>
                      <th>Código da URL</th>
                      <th>Peso</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSiglario.map(item => (
                      <tr key={item.sigla}>
                        <td><strong style={{ color: '#c9a96e' }}>{item.sigla}</strong></td>
                        <td>{item.title}</td>
                        <td><span className="adm-badge">{item.category}</span></td>
                        <td>
                          {item.url_code ? (
                            <code style={{ background: '#0d1117', padding: '2px 6px', borderRadius: '4px', fontSize: '11px' }}>
                              {item.url_code}
                            </code>
                          ) : '-'}
                        </td>
                        <td>{item.weight}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              className="adm-delete-btn"
                              style={{ color: '#7ec8e0' }}
                              onClick={() => {
                                setEditingSigla(item);
                                setIsSiglarioModalOpen(true);
                              }}
                              title="Editar"
                            >
                              <Edit2 size={13} />
                            </button>
                            <button
                              className="adm-delete-btn"
                              onClick={() => handleDeleteSiglario(item.sigla)}
                              title="Remover"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* --- SECTION: BLESSED --- */}
        {activeSection === 'blessed' && (
          <div className="adm-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', gap: '16px' }}>
              <div className="adm-search-wrap" style={{ flex: 1, position: 'relative', maxWidth: '400px' }}>
                <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b949e' }} />
                <input 
                  type="text" 
                  placeholder="Pesquisar perguntas e respostas curadas..." 
                  value={searchBlessedQuery}
                  onChange={e => setSearchBlessedQuery(e.target.value)}
                  className="adm-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
              
              <button 
                className="adm-cta-btn" 
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                onClick={() => {
                  setEditingBlessed(null);
                  setNewBlessed({ question: '', answer: '' });
                  setIsBlessedModalOpen(true);
                }}
              >
                <Plus size={14} /> Curar Resposta
              </button>
            </div>

            <div className="adm-table-wrap">
              {isLoadingBlessed && blessedList.length === 0 ? (
                <div className="adm-empty-state">
                  <Loader size={24} className="spinning" />
                  <p>Acessando base de especialistas...</p>
                </div>
              ) : filteredBlessed.length === 0 ? (
                <div className="adm-empty-state">
                  <HelpCircle size={40} style={{ opacity: 0.3 }} />
                  <p>Nenhuma resposta validada encontrada.</p>
                </div>
              ) : (
                <table className="adm-table">
                  <thead>
                    <tr>
                      <th style={{ width: '30%' }}>Pergunta de Usuário</th>
                      <th style={{ width: '45%' }}>Resposta de Especialista (Injetada)</th>
                      <th style={{ width: '15%' }}>Data</th>
                      <th style={{ width: '10%' }}>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBlessed.map(item => (
                      <tr key={item.id}>
                        <td>
                          <div style={{ fontWeight: 500, color: '#e6edf3', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <span>{item.question}</span>
                          </div>
                        </td>
                        <td>
                          <div style={{ color: '#8b949e', fontSize: '12px', maxHeight: '80px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                            {item.answer}
                          </div>
                        </td>
                        <td className="adm-num-cell" style={{ fontSize: '11px' }}>{formatDate(item.date)}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              className="adm-delete-btn"
                              style={{ color: '#7ec8e0' }}
                              onClick={() => {
                                setEditingBlessed(item);
                                setIsBlessedModalOpen(true);
                              }}
                              title="Editar"
                            >
                              <Edit2 size={13} />
                            </button>
                            <button
                              className="adm-delete-btn"
                              onClick={() => handleDeleteBlessed(item.id)}
                              title="Excluir"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* --- SECTION: LOGS --- */}
        {activeSection === 'logs' && (
          <div className="adm-content">
            {/* Warning if using fallback logs */}
            {usingFallbackLogs && (
              <div className="adm-feedback adm-feedback--error" style={{ marginBottom: '16px', borderStyle: 'dashed' }}>
                <AlertCircle size={16} />
                <span>
                  <strong>Aviso:</strong> Mostrando logs acumulados via fallback local (JSON no backend), já que a tabela remota `search_logs` está inacessível.
                </span>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div className="adm-search-wrap" style={{ flex: 1, position: 'relative', maxWidth: '400px' }}>
                <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#8b949e' }} />
                <input 
                  type="text" 
                  placeholder="Pesquisar consultas ou comentários de feedback..." 
                  value={searchLogQuery}
                  onChange={e => setSearchLogQuery(e.target.value)}
                  className="adm-input"
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            <div className="adm-table-wrap">
              {isLoadingLogs && logsList.length === 0 ? (
                <div className="adm-empty-state">
                  <Loader size={24} className="spinning" />
                  <p>Acessando logs de auditoria...</p>
                </div>
              ) : filteredLogs.length === 0 ? (
                <div className="adm-empty-state">
                  <MessageSquare size={40} style={{ opacity: 0.3 }} />
                  <p>Nenhum log correspondente encontrado.</p>
                </div>
              ) : (
                <table className="adm-table">
                  <thead>
                    <tr>
                      <th style={{ width: '30%' }}>Consulta</th>
                      <th>Intenção</th>
                      <th>Confiança</th>
                      <th>Fontes</th>
                      <th>Feedback</th>
                      <th>Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLogs.map((item, idx) => (
                      <tr key={item.id || idx}>
                        <td>
                          <div style={{ fontWeight: 500, color: '#e6edf3', fontSize: '13px' }}>
                            "{item.query}"
                          </div>
                        </td>
                        <td>
                          <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#c9a96e' }}>
                            {item.intent || 'GERAL'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <span style={{ 
                              fontWeight: 600,
                              color: item.confidence_level === 'Alta' ? '#3fb950' : item.confidence_level === 'Média' ? '#7ec8e0' : '#ff6b6b'
                            }}>
                              {item.confidence_level || 'Média'}
                            </span>
                            <span style={{ fontSize: '10px', color: '#8b949e' }}>
                              {item.confidence_pct}%
                            </span>
                          </div>
                        </td>
                        <td className="adm-num-cell">{item.num_citations || 0} refs</td>
                        <td>
                          {item.feedback ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                              <span style={{ 
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                fontSize: '11px',
                                fontWeight: 600,
                                color: item.feedback === 'positivo' ? '#3fb950' : '#ff6b6b'
                              }}>
                                {item.feedback === 'positivo' ? <ThumbsUp size={10} /> : <ThumbsDown size={10} />}
                                {item.feedback.toUpperCase()}
                              </span>
                              {item.feedback_comment && (
                                <span style={{ fontSize: '10px', color: '#8b949e', fontStyle: 'italic', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block', whiteSpace: 'nowrap' }} title={item.feedback_comment}>
                                  "{item.feedback_comment}"
                                </span>
                              )}
                            </div>
                          ) : (
                            <span style={{ color: '#484f58', fontSize: '11px' }}>Nenhum</span>
                          )}
                        </td>
                        <td className="adm-num-cell" style={{ fontSize: '11px', whiteSpace: 'nowrap' }}>
                          {formatDate(item.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

      </main>

      {/* ────────────────────────────────────────────
         MODAL: DOCUMENT CHUNKS DETAIL
      ──────────────────────────────────────────── */}
      {isChunksModalOpen && selectedDoc && (
        <div className="adm-modal-overlay">
          <div className="adm-modal-content adm-modal-content--large">
            <div className="adm-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FileText size={18} className="adm-gold" />
                <div>
                  <h3 className="adm-modal-title">{selectedDoc.title}</h3>
                  <span className="adm-modal-subtitle">
                    Sigla: <strong style={{ color: '#c9a96e' }}>{selectedDoc.sigla}</strong> · {docChunks.length} fragmentos ativos na base vetorial
                  </span>
                </div>
              </div>
              <button className="adm-modal-close" onClick={() => {
                setIsChunksModalOpen(false);
                setSelectedDoc(null);
                setDocChunks([]);
              }}><X size={18} /></button>
            </div>
            
            <div className="adm-modal-body" style={{ maxHeight: '60vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
              {isLoadingChunks ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '40px 0', gap: '8px' }}>
                  <Loader size={20} className="spinning adm-gold" />
                  <span style={{ color: '#8b949e', fontSize: '13px' }}>Carregando dados da coleção vetorial...</span>
                </div>
              ) : docChunks.length === 0 ? (
                <p style={{ color: '#8b949e', fontSize: '13px', textAlign: 'center' }}>Nenhum detalhe do chunk retornado pelo banco.</p>
              ) : (
                docChunks.map((chunk, idx) => (
                  <div key={chunk.id || idx} style={{ background: '#0d1117', border: '1px solid #21262d', borderRadius: '8px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #21262d', paddingBottom: '8px', marginBottom: '10px', fontSize: '11px', color: '#8b949e' }}>
                      <span>Fragmento #{chunk.metadata?.chunk_index ?? idx + 1}</span>
                      <span style={{ fontFamily: 'monospace' }}>ID: {chunk.id}</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#c9d1d9', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {chunk.content}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────
         MODAL: SIGLARIO CREATE/EDIT
      ──────────────────────────────────────────── */}
      {isSiglarioModalOpen && (
        <div className="adm-modal-overlay">
          <div className="adm-modal-content">
            <div className="adm-modal-header">
              <h3 className="adm-modal-title">
                {editingSigla ? 'Editar Item do Siglário' : 'Novo Item no Siglário'}
              </h3>
              <button className="adm-modal-close" onClick={() => {
                setIsSiglarioModalOpen(false);
                setEditingSigla(null);
              }}><X size={18} /></button>
            </div>
            
            <form onSubmit={handleSaveSiglario}>
              <div className="adm-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
                <div className="adm-meta-field">
                  <label>Sigla (Abreviatura)</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingSigla}
                    placeholder="Ex: NQT"
                    value={editingSigla ? editingSigla.sigla : newSigla.sigla}
                    onChange={e => setNewSigla({ ...newSigla, sigla: e.target.value.toUpperCase() })}
                    className="adm-input"
                  />
                  {!editingSigla && <span style={{ fontSize: '10px', color: '#8b949e' }}>A sigla identifica a obra nos arquivos PDFs associados.</span>}
                </div>

                <div className="adm-meta-field">
                  <label>Título Descritivo da Obra</label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: Notas Quotidianas do Padre Dehon"
                    value={editingSigla ? editingSigla.title : newSigla.title}
                    onChange={e => {
                      if (editingSigla) setEditingSigla({ ...editingSigla, title: e.target.value });
                      else setNewSigla({ ...newSigla, title: e.target.value });
                    }}
                    className="adm-input"
                  />
                </div>

                <div className="adm-meta-field">
                  <label>Categoria da Obra</label>
                  <select
                    value={editingSigla ? editingSigla.category : newSigla.category}
                    onChange={e => {
                      if (editingSigla) setEditingSigla({ ...editingSigla, category: e.target.value });
                      else setNewSigla({ ...newSigla, category: e.target.value });
                    }}
                    className="adm-input"
                    style={{ background: '#161b22', border: '1px solid #30363d', color: '#f0f6fc' }}
                  >
                    <option value="Obras Espirituais">Obras Espirituais</option>
                    <option value="Obras Sociais">Obras Sociais</option>
                    <option value="Diários">Diários</option>
                    <option value="Viagens">Viagens</option>
                    <option value="Outros">Outros</option>
                  </select>
                </div>

                <div className="adm-meta-grid" style={{ gridTemplateColumns: '1fr 100px', marginBottom: 0 }}>
                  <div className="adm-meta-field">
                    <label>Código da URL (opcional)</label>
                    <input
                      type="text"
                      placeholder="Ex: dehon-nqt"
                      value={editingSigla ? editingSigla.url_code : newSigla.url_code}
                      onChange={e => {
                        if (editingSigla) setEditingSigla({ ...editingSigla, url_code: e.target.value });
                        else setNewSigla({ ...newSigla, url_code: e.target.value });
                      }}
                      className="adm-input"
                    />
                  </div>
                  <div className="adm-meta-field">
                    <label>Peso (1-10)</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      required
                      value={editingSigla ? editingSigla.weight : newSigla.weight}
                      onChange={e => {
                        const val = Math.max(1, Math.min(10, Number(e.target.value)));
                        if (editingSigla) setEditingSigla({ ...editingSigla, weight: val });
                        else setNewSigla({ ...newSigla, weight: val });
                      }}
                      className="adm-input"
                    />
                  </div>
                </div>
              </div>
              
              <div className="adm-modal-footer" style={{ padding: '16px 20px', borderTop: '1px solid #21262d', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" className="adm-delete-btn" style={{ color: '#8b949e', borderColor: '#30363d' }} onClick={() => {
                  setIsSiglarioModalOpen(false);
                  setEditingSigla(null);
                }}>
                  Cancelar
                </button>
                <button type="submit" className="adm-cta-btn">
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ────────────────────────────────────────────
         MODAL: BLESSED CREATE/EDIT
      ──────────────────────────────────────────── */}
      {isBlessedModalOpen && (
        <div className="adm-modal-overlay">
          <div className="adm-modal-content adm-modal-content--large">
            <div className="adm-modal-header">
              <h3 className="adm-modal-title">
                {editingBlessed ? 'Editar Resposta Validada' : 'Curar Nova Resposta RAG'}
              </h3>
              <button className="adm-modal-close" onClick={() => {
                setIsBlessedModalOpen(false);
                setEditingBlessed(null);
              }}><X size={18} /></button>
            </div>
            
            <form onSubmit={handleSaveBlessed}>
              <div className="adm-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}>
                <div className="adm-meta-field">
                  <label>Pergunta de Usuário (Gatilho Exato/Similar)</label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: O que o Padre Dehon diz sobre o Sagrado Coração?"
                    value={editingBlessed ? editingBlessed.question : newBlessed.question}
                    onChange={e => {
                      if (editingBlessed) setEditingBlessed({ ...editingBlessed, question: e.target.value });
                      else setNewBlessed({ ...newBlessed, question: e.target.value });
                    }}
                    className="adm-input"
                  />
                  <span style={{ fontSize: '10px', color: '#8b949e' }}>Se um usuário fizer esta pergunta ou uma muito similar, a resposta curada será injetada para guiar o tom e conteúdo do RAG.</span>
                </div>

                <div className="adm-meta-field">
                  <label>Resposta de Especialista / Doutrina Curada</label>
                  <textarea
                    required
                    rows={8}
                    placeholder="Digite a resposta acadêmica ideal, incluindo o estilo de citação correto das obras do Padre Dehon."
                    value={editingBlessed ? editingBlessed.answer : newBlessed.answer}
                    onChange={e => {
                      if (editingBlessed) setEditingBlessed({ ...editingBlessed, answer: e.target.value });
                      else setNewBlessed({ ...newBlessed, answer: e.target.value });
                    }}
                    className="adm-input"
                    style={{ resize: 'vertical', fontFamily: 'inherit', lineHeight: 1.5 }}
                  />
                </div>
              </div>
              
              <div className="adm-modal-footer" style={{ padding: '16px 20px', borderTop: '1px solid #21262d', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" className="adm-delete-btn" style={{ color: '#8b949e', borderColor: '#30363d' }} onClick={() => {
                  setIsBlessedModalOpen(false);
                  setEditingBlessed(null);
                }}>
                  Cancelar
                </button>
                <button type="submit" className="adm-cta-btn">
                  Salvar Resposta Curada
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
