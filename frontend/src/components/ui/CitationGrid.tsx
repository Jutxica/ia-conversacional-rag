import React from 'react';
import './CitationGrid.css';
import { ExternalLink, FileText } from 'lucide-react';

interface Citation {
  id: string | number;
  title: string;
  url?: string;
  page_url?: string;
  snippet?: string;
  sigla?: string;
  score?: number;
}

interface CitationGridProps {
  citations: Citation[];
}

const CitationGrid: React.FC<CitationGridProps> = ({ citations }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="citation-grid">
      {citations.map((citation, idx) => (
        <div key={citation.id || idx} className="citation-card" onClick={() => citation.url && window.open(citation.url, '_blank')}>
          <div className="citation-header">
            <span className="citation-tag">{citation.sigla || 'DOC'}</span>
            {citation.score && (
              <span className="citation-score">Rel {Math.round(citation.score * 100)}%</span>
            )}
          </div>
          <h4 className="citation-title">{citation.title}</h4>
          {citation.snippet && (
            <p className="citation-snippet">"{citation.snippet}"</p>
          )}
          <div className="citation-footer">
            <div className="citation-link">
              <FileText size={14} />
              <span>Ver Documento</span>
            </div>
            <ExternalLink size={14} />
          </div>
        </div>
      ))}
    </div>
  );
};

export default CitationGrid;
