import React, { useState, useRef, useEffect } from 'react';
import { X, Camera, User } from 'lucide-react';
import './ProfileModal.css';

export interface UserProfile {
  name: string;
  photoUrl: string;
  title: 'Padre' | 'Leigo' | 'Religioso de votos simples';
  congregation: 'Dehoniano' | 'Outra congregação';
}

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: UserProfile;
  onSave: (updated: UserProfile) => void;
}

export default function ProfileModal({ isOpen, onClose, profile, onSave }: ProfileModalProps) {
  const [name, setName] = useState(profile.name);
  const [photoUrl, setPhotoUrl] = useState(profile.photoUrl);
  const [title, setTitle] = useState(profile.title);
  const [congregation, setCongregation] = useState(profile.congregation);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setName(profile.name);
    setPhotoUrl(profile.photoUrl);
    setTitle(profile.title);
    setCongregation(profile.congregation);
  }, [profile, isOpen]);

  if (!isOpen) return null;

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        alert("Por favor, selecione uma imagem menor que 2MB.");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleRemovePhoto = () => {
    setPhotoUrl('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert("Por favor, digite seu nome.");
      return;
    }
    onSave({
      name: name.trim(),
      photoUrl,
      title,
      congregation
    });
    onClose();
  };

  return (
    <div className="pm-overlay">
      <div className="pm-container">
        <header className="pm-header">
          <h2>Configuração de Perfil</h2>
          <button className="pm-close-btn" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="pm-form">
          {/* Avatar Section */}
          <div className="pm-avatar-section">
            <div className="pm-avatar-container" onClick={triggerFileInput} title="Alterar foto de perfil">
              {photoUrl ? (
                <img src={photoUrl} alt="Avatar Preview" className="pm-avatar-img" />
              ) : (
                <div className="pm-avatar-placeholder">
                  <User size={40} />
                </div>
              )}
              <div className="pm-avatar-hover">
                <Camera size={20} />
              </div>
            </div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handlePhotoUpload}
              accept="image/*"
              style={{ display: 'none' }}
            />
            <div className="pm-avatar-actions">
              <button type="button" className="pm-upload-btn" onClick={triggerFileInput}>
                Escolher Foto
              </button>
              {photoUrl && (
                <button type="button" className="pm-remove-photo-btn" onClick={handleRemovePhoto}>
                  Remover
                </button>
              )}
            </div>
          </div>

          {/* Form Fields */}
          <div className="pm-fields">
            <div className="pm-field-group">
              <label htmlFor="pm-name-input">Nome Exibido</label>
              <input
                id="pm-name-input"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Utxica"
                maxLength={40}
                className="pm-input"
                required
              />
              <span className="pm-field-hint">Como você gostaria de ser chamado(a) no sistema.</span>
            </div>

            <div className="pm-field-group">
              <label>Vocação / Título</label>
              <div className="pm-radio-group">
                <label className={`pm-radio-card ${title === 'Leigo' ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="title"
                    value="Leigo"
                    checked={title === 'Leigo'}
                    onChange={() => setTitle('Leigo')}
                  />
                  <span>Leigo(a)</span>
                </label>
                <label className={`pm-radio-card ${title === 'Padre' ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="title"
                    value="Padre"
                    checked={title === 'Padre'}
                    onChange={() => setTitle('Padre')}
                  />
                  <span>Padre</span>
                </label>
                <label className={`pm-radio-card ${title === 'Religioso de votos simples' ? 'active' : ''}`}>
                  <input
                    type="radio"
                    name="title"
                    value="Religioso de votos simples"
                    checked={title === 'Religioso de votos simples'}
                    onChange={() => setTitle('Religioso de votos simples')}
                  />
                  <span>Religioso (Frater)</span>
                </label>
              </div>
            </div>

            {title !== 'Leigo' && (
              <div className="pm-field-group pm-fade-in">
                <label>Filiação / Congregação</label>
                <div className="pm-radio-group">
                  <label className={`pm-radio-card ${congregation === 'Dehoniano' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="congregation"
                      value="Dehoniano"
                      checked={congregation === 'Dehoniano'}
                      onChange={() => setCongregation('Dehoniano')}
                    />
                    <span>Dehoniano (scj)</span>
                  </label>
                  <label className={`pm-radio-card ${congregation === 'Outra congregação' ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="congregation"
                      value="Outra congregação"
                      checked={congregation === 'Outra congregação'}
                      onChange={() => setCongregation('Outra congregação')}
                    />
                    <span>Outra Congregação / Diocese</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          <footer className="pm-footer">
            <button type="button" className="pm-cancel-btn" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="pm-save-btn">
              Salvar Alterações
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}
