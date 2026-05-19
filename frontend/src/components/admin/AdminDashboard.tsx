import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Upload, FileText, Trash2, RefreshCw, CheckCircle, AlertTriangle, Loader, Database, X } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace('/api/chat', '') : '';

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

export default function AdminDashboard({ onClose }: { onClose: () => void }) {
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [upload, setUpload] = useState<UploadState>({ status: 'idle', message: '' });
  const [sigla, setSigla] = useState('PDF');
  const [docTitle, setDocTitle] = useState('');
  const [weight, setWeight] = useState(5);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents`, {
      });
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

    setUpload({ status: 'uploading', message: `Processando "${file.name}" com Firecrawl...` });

    const formData = new FormData();
    formData.append('file', file);
    formData.append('sigla', sigla);
    formData.append('document_weight', String(weight));
    if (docTitle.trim()) formData.append('title', docTitle.trim());

    try {
      const res = await fetch(`${API_BASE}/api/admin/upload`, {
        method: 'POST',
        body: formData
      });

      const data = await res.json();

      if (!res.ok) {
        setUpload({ status: 'error', message: data.detail || 'Erro desconhecido no servidor.' });
        return;
      }

      setUpload({
        status: 'success',
        message: `"${data.document}" ingerido com sucesso!`,
        chunks: data.chunks_inserted
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
  }, [sigla, docTitle, weight]);

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);

  const handleDelete = async (sourceId: string) => {
    if (!confirm(`Remover todos os chunks de "${sourceId}" do corpus?`)) return;
    setDeletingId(sourceId);
    try {
      const res = await fetch(`${API_BASE}/api/admin/documents/${encodeURIComponent(sourceId)}`, {
        method: 'DELETE',
      });
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
    if (n >= 5) return '#7ec8c8';
    return '#8b9bb4';
  };

  return (
    <div className="admin-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="admin-panel">
        {/* Header */}
        <div className="admin-header">
          <div className="admin-title">
            <Database size={20} />
            <span>Gestão do Corpus Dehoniano</span>
          </div>
          <button className="admin-close" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Stats Bar */}
        <div className="admin-stats">
          <div className="stat-item">
            <span className="stat-number">{documents.length}</span>
            <span className="stat-label">documentos</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-number">{totalChunks.toLocaleString('pt-BR')}</span>
            <span className="stat-label">fragmentos indexados</span>
          </div>
          <button className="admin-refresh" onClick={fetchDocuments} title="Atualizar lista">
            <RefreshCw size={14} className={isLoading ? 'spinning' : ''} />
          </button>
        </div>

        {/* Upload Zone */}
        <div className="admin-section">
          <h3 className="admin-section-title">Adicionar Novo Documento</h3>

          <div className="upload-meta-grid">
            <div className="upload-field">
              <label>Título (opcional)</label>
              <input
                type="text"
                placeholder="Ex: Cartas Sacerdotais 1905"
                value={docTitle}
                onChange={e => setDocTitle(e.target.value)}
                className="admin-input"
              />
            </div>
            <div className="upload-field">
              <label>Sigla</label>
              <input
                type="text"
                placeholder="Ex: NQT, CIG, PDF"
                value={sigla}
                maxLength={10}
                onChange={e => setSigla(e.target.value.toUpperCase())}
                className="admin-input admin-input-sm"
              />
            </div>
            <div className="upload-field">
              <label>Peso ({weight})</label>
              <input
                type="range"
                min={1}
                max={10}
                value={weight}
                onChange={e => setWeight(Number(e.target.value))}
                className="admin-range"
              />
            </div>
          </div>

          <div
            className={`upload-dropzone ${isDragging ? 'dragging' : ''} ${upload.status === 'uploading' ? 'uploading' : ''}`}
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
              <div className="upload-progress">
                <Loader size={28} className="spinning gold" />
                <p>{upload.message}</p>
                <span className="upload-hint">Firecrawl está extraindo e vetorizando o documento...</span>
              </div>
            ) : (
              <div className="upload-idle">
                <Upload size={28} />
                <p>Arraste um PDF aqui ou clique para selecionar</p>
                <span className="upload-hint">Suportado: PDF até 100MB</span>
              </div>
            )}
          </div>

          {/* Upload Feedback */}
          {upload.status === 'success' && (
            <div className="upload-feedback success">
              <CheckCircle size={16} />
              <span>{upload.message}</span>
              {upload.chunks !== undefined && (
                <span className="feedback-detail">· {upload.chunks} fragmentos criados</span>
              )}
              <button onClick={() => setUpload({ status: 'idle', message: '' })}><X size={14} /></button>
            </div>
          )}
          {upload.status === 'error' && (
            <div className="upload-feedback error">
              <AlertTriangle size={16} />
              <span>{upload.message}</span>
              <button onClick={() => setUpload({ status: 'idle', message: '' })}><X size={14} /></button>
            </div>
          )}
        </div>

        {/* Document List */}
        <div className="admin-section">
          <h3 className="admin-section-title">Corpus Indexado</h3>
          {isLoading && documents.length === 0 ? (
            <div className="admin-loading"><Loader size={20} className="spinning" /><span>Carregando corpus...</span></div>
          ) : documents.length === 0 ? (
            <div className="admin-empty">
              <FileText size={32} />
              <p>Nenhum documento no corpus ainda.</p>
            </div>
          ) : (
            <div className="doc-list">
              {documents.map(doc => (
                <div key={doc.source_id} className="doc-item">
                  <div className="doc-icon"><FileText size={16} /></div>
                  <div className="doc-info">
                    <span className="doc-title">{doc.title || doc.source_id}</span>
                    <div className="doc-meta">
                      <span className="doc-sigla">{doc.sigla}</span>
                      <span className="doc-chunks">{doc.chunks} fragmentos</span>
                      <span
                        className="doc-weight"
                        style={{ color: weightColor(doc.document_weight) }}
                      >
                        peso {doc.document_weight}
                      </span>
                    </div>
                  </div>
                  <button
                    className="doc-delete"
                    onClick={() => handleDelete(doc.source_id)}
                    disabled={deletingId === doc.source_id}
                    title="Remover do corpus"
                  >
                    {deletingId === doc.source_id
                      ? <Loader size={14} className="spinning" />
                      : <Trash2 size={14} />
                    }
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
