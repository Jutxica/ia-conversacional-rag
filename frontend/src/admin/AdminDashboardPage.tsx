import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Upload, FileText, Trash2, RefreshCw, CheckCircle, AlertTriangle, Loader, Database, LogOut, LayoutDashboard, Settings } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL?.replace('/api/chat', '') || 'http://localhost:8000';

interface DocItem {
  source_id: string;
  title: string;
  sigla: string;
  document_weight: number | string;
  chunks: number;
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
}

export default function AdminDashboardPage({ token, onLogout }: Props) {
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [upload, setUpload] = useState<UploadState>({ status: 'idle', message: '' });
  const [sigla, setSigla] = useState('PDF');
  const [docTitle, setDocTitle] = useState('');
  const [weight, setWeight] = useState(5);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'corpus' | 'upload'>('corpus');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const authHeaders = { Authorization: `Bearer ${token}` };

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents`, { headers: authHeaders });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (e: any) {
      console.error('Erro ao buscar documentos:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchDocuments(); }, []);

  const handleUpload = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUpload({ status: 'error', message: 'Apenas arquivos PDF são aceitos.' });
      return;
    }

    setActiveSection('upload');
    setUpload({ status: 'uploading', message: `Processando "${file.name}" com Firecrawl...` });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('sigla', sigla);
    formData.append('document_weight', String(weight));
    if (docTitle.trim()) formData.append('title', docTitle.trim());

    try {
      const res = await fetch(`${API_BASE}/api/admin/upload`, {
        method: 'POST',
        headers: authHeaders,
        body: formData,
      });

      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      const data = await res.json();

      if (!res.ok) {
        setUpload({ status: 'error', message: data.detail || 'Erro desconhecido no servidor.' });
        return;
      }

      setUpload({
        status: 'success',
        message: `"${data.document}" ingerido com sucesso!`,
        chunks: data.chunks_inserted,
      });
      setDocTitle('');
      setSigla('PDF');
      setWeight(5);
      fetchDocuments();
    } catch (e: any) {
      setUpload({ status: 'error', message: `Erro de conexão: ${e.message}` });
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

  const handleDelete = async (sourceId: string) => {
    if (!confirm(`Remover todos os chunks de "${sourceId}" do corpus?`)) return;
    setDeletingId(sourceId);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents/${encodeURIComponent(sourceId)}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (res.status === 401 || res.status === 403) { onLogout(); return; }
      const data = await res.json();
      if (res.ok) {
        setDocuments(prev => prev.filter(d => d.source_id !== sourceId));
        setTotalChunks(prev => prev - (data.chunks_deleted || 0));
      }
    } catch (e) {
      console.error('Erro ao deletar:', e);
    } finally {
      setDeletingId(null);
    }
  };

  const weightColor = (w: number | string) => {
    const n = Number(w);
    if (n >= 8) return '#c9a96e';
    if (n >= 5) return '#7ec8e0';
    return '#8b9bb4';
  };

  return (
    <div className="adm-root">
      {/* Sidebar */}
      <aside className="adm-sidebar">
        <div className="adm-sidebar-brand">
          <div className="adm-brand-logo">D</div>
          <div>
            <div className="adm-brand-name">Dehon AI</div>
            <div className="adm-brand-sub">Admin</div>
          </div>
        </div>

        <nav className="adm-nav">
          <button
            className={`adm-nav-item ${activeSection === 'corpus' ? 'active' : ''}`}
            onClick={() => setActiveSection('corpus')}
          >
            <Database size={16} />
            <span>Corpus</span>
          </button>
          <button
            className={`adm-nav-item ${activeSection === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveSection('upload')}
          >
            <Upload size={16} />
            <span>Ingestão</span>
          </button>
        </nav>

        <button className="adm-logout" onClick={onLogout}>
          <LogOut size={15} />
          <span>Sair</span>
        </button>
      </aside>

      {/* Main Content */}
      <main className="adm-main">
        {/* Top Bar */}
        <div className="adm-topbar">
          <div className="adm-topbar-left">
            <h1 className="adm-page-title">
              {activeSection === 'corpus' ? 'Corpus Dehoniano' : 'Ingestão de Documentos'}
            </h1>
            <p className="adm-page-desc">
              {activeSection === 'corpus'
                ? `${documents.length} documentos · ${totalChunks.toLocaleString('pt-BR')} fragmentos indexados`
                : 'Adicione PDFs ao banco vetorial via Firecrawl'}
            </p>
          </div>
          <button
            className="adm-refresh-btn"
            onClick={fetchDocuments}
            title="Atualizar"
          >
            <RefreshCw size={15} className={isLoading ? 'spinning' : ''} />
          </button>
        </div>

        {/* Corpus Section */}
        {activeSection === 'corpus' && (
          <div className="adm-content">
            {/* Stats Cards */}
            <div className="adm-stats-row">
              <div className="adm-stat-card">
                <span className="adm-stat-num">{documents.length}</span>
                <span className="adm-stat-lbl">Documentos</span>
              </div>
              <div className="adm-stat-card">
                <span className="adm-stat-num">{totalChunks.toLocaleString('pt-BR')}</span>
                <span className="adm-stat-lbl">Fragmentos indexados</span>
              </div>
              <div className="adm-stat-card adm-stat-card--action" onClick={() => setActiveSection('upload')}>
                <Upload size={20} style={{ color: '#c9a96e' }} />
                <span className="adm-stat-lbl" style={{ color: '#c9a96e' }}>Adicionar PDF</span>
              </div>
            </div>

            {/* Document Table */}
            <div className="adm-table-wrap">
              {isLoading && documents.length === 0 ? (
                <div className="adm-empty-state">
                  <Loader size={24} className="spinning" />
                  <p>Carregando corpus...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="adm-empty-state">
                  <FileText size={40} style={{ opacity: 0.3 }} />
                  <p>Nenhum documento no corpus ainda.</p>
                  <button className="adm-cta-btn" onClick={() => setActiveSection('upload')}>
                    Adicionar primeiro documento
                  </button>
                </div>
              ) : (
                <table className="adm-table">
                  <thead>
                    <tr>
                      <th>Documento</th>
                      <th>Sigla</th>
                      <th>Fragmentos</th>
                      <th>Peso</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map(doc => (
                      <tr key={doc.source_id}>
                        <td>
                          <div className="adm-doc-cell">
                            <FileText size={14} className="adm-doc-icon" />
                            <span className="adm-doc-title">{doc.title || doc.source_id}</span>
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
                          <button
                            className="adm-delete-btn"
                            onClick={() => handleDelete(doc.source_id)}
                            disabled={deletingId === doc.source_id}
                            title="Remover do corpus"
                          >
                            {deletingId === doc.source_id
                              ? <Loader size={13} className="spinning" />
                              : <Trash2 size={13} />
                            }
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* Upload Section */}
        {activeSection === 'upload' && (
          <div className="adm-content">
            <div className="adm-upload-wrap">
              {/* Metadata */}
              <div className="adm-meta-grid">
                <div className="adm-meta-field">
                  <label>Título do documento</label>
                  <input
                    type="text"
                    placeholder="Ex: Cartas Sacerdotais 1905"
                    value={docTitle}
                    onChange={e => setDocTitle(e.target.value)}
                    className="adm-input"
                  />
                </div>
                <div className="adm-meta-field adm-meta-field--sm">
                  <label>Sigla</label>
                  <input
                    type="text"
                    placeholder="NQT"
                    value={sigla}
                    maxLength={10}
                    onChange={e => setSigla(e.target.value.toUpperCase())}
                    className="adm-input"
                  />
                </div>
                <div className="adm-meta-field adm-meta-field--sm">
                  <label>Peso semântico ({weight})</label>
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

              {/* Drop Zone */}
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
                    <span className="adm-dz-hint">Firecrawl está extraindo e vetorizando...</span>
                    <div className="adm-progress-bar">
                      <div className="adm-progress-fill" />
                    </div>
                  </div>
                ) : (
                  <div className="adm-dz-content">
                    <Upload size={32} className="adm-dz-icon" />
                    <p className="adm-dz-title">Arraste um PDF aqui ou clique para selecionar</p>
                    <span className="adm-dz-hint">PDF até 100MB · O conteúdo será extraído, chunked e vetorizado automaticamente</span>
                  </div>
                )}
              </div>

              {/* Feedback */}
              {upload.status === 'success' && (
                <div className="adm-feedback adm-feedback--success">
                  <CheckCircle size={16} />
                  <span>{upload.message}</span>
                  {upload.chunks !== undefined && (
                    <span className="adm-feedback-detail">· {upload.chunks.toLocaleString('pt-BR')} fragmentos criados</span>
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
      </main>
    </div>
  );
}
