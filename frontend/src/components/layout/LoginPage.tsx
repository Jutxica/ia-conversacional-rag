import React, { useState, useEffect } from 'react';
import './LoginPage.css';
import { ShieldCheck, Loader2, Mail, Lock, User, Phone, Eye, EyeOff, BookOpen, ArrowRight } from 'lucide-react';
import { supabase } from '../../supabaseClient';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [countryCode, setCountryCode] = useState('+55');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const countries = [
    { code: '+55', flag: '🇧🇷', name: 'Brasil' },
    { code: '+39', flag: '🇮🇹', name: 'Itália' },
    { code: '+33', flag: '🇫🇷', name: 'França' },
    { code: '+49', flag: '🇩🇪', name: 'Alemanha' },
    { code: '+1', flag: '🇺🇸', name: 'EUA/Canadá' },
    { code: '+34', flag: '🇪🇸', name: 'Espanha' },
    { code: '+351', flag: '🇵🇹', name: 'Portugal' },
    { code: '+54', flag: '🇦🇷', name: 'Argentina' },
  ];

  // Clear messages on mode switch
  useEffect(() => {
    setError(null);
    setSuccess(null);
  }, [mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (mode === 'signup') {
        if (password !== confirmPassword) {
          setError('As senhas não coincidem.');
          setLoading(false);
          return;
        }
        if (password.length < 6) {
          setError('A senha deve ter pelo menos 6 caracteres.');
          setLoading(false);
          return;
        }
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              full_name: fullName,
              phone: `${countryCode} ${phone}`
            }
          }
        });
        if (error) throw error;
        setSuccess('Conta criada com sucesso! Verifique seu e-mail para ativar.');
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        onLoginSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Erro na autenticação.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-overlay">
      {/* Animated Background Orbs */}
      <div className="login-bg-orbs">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      {/* Split Layout */}
      <div className="login-split">
        {/* Left: Brand Panel */}
        <div className="login-brand-panel">
          <div className="brand-content animate-fade-in">
            <h1 className="brand-title">Biblioteca Dehoniana</h1>
            <p className="brand-motto">"Sint unum: A inteligência a serviço do Coração."</p>
            
            <div className="brand-footer">
              <span>Sistema de Alta Pesquisa desenvolvido por</span>
              <strong>Fr. João Rodrigues Utxica, scj</strong>
            </div>
          </div>
        </div>

        {/* Right: Auth Card */}
        <div className="login-form-panel">
          <div className="login-card animate-slide-up">
            <div className="login-card-header">
              <img src="/Navbar.png" className="login-logo" alt="Dehon AI" />
              <h2>{mode === 'login' ? 'Bem-vindo de volta' : 'Criar nova conta'}</h2>
              <p>{mode === 'login' 
                ? 'Acesse sua conta para continuar pesquisando.' 
                : 'Junte-se à comunidade de pesquisadores Dehonianos.'}</p>
            </div>
            
            {/* Segmented Tabs */}
            <div className="auth-tabs">
              <button
                className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
                onClick={() => setMode('login')}
                type="button"
                id="tab-login"
              >Entrar</button>
              <button
                className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
                onClick={() => setMode('signup')}
                type="button"
                id="tab-signup"
              >Criar Conta</button>
              <div className={`tab-indicator ${mode === 'signup' ? 'right' : 'left'}`} />
            </div>

            <form className="login-form" onSubmit={handleSubmit}>
              {mode === 'signup' && (
                <>
                  <div className={`input-group ${focusedField === 'name' ? 'focused' : ''}`}>
                    <label htmlFor="fullName">Nome Completo</label>
                    <div className="input-with-icon">
                      <User size={18} className="input-icon" />
                      <input 
                        id="fullName"
                        type="text" 
                        className="login-input" 
                        placeholder="Seu nome completo" 
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        onFocus={() => setFocusedField('name')}
                        onBlur={() => setFocusedField(null)}
                      />
                    </div>
                  </div>
                  <div className={`input-group ${focusedField === 'phone' ? 'focused' : ''}`}>
                    <label htmlFor="phone">Telefone</label>
                    <div className="phone-input-container">
                      <select 
                        className="country-select"
                        value={countryCode}
                        onChange={(e) => setCountryCode(e.target.value)}
                        aria-label="Código do país"
                      >
                        {countries.map(c => (
                          <option key={c.code} value={c.code}>
                            {c.flag} {c.code}
                          </option>
                        ))}
                      </select>
                      <div className="input-with-icon">
                        <Phone size={18} className="input-icon" />
                        <input 
                          id="phone"
                          type="tel" 
                          className="login-input" 
                          placeholder="(00) 00000-0000" 
                          required
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                          onFocus={() => setFocusedField('phone')}
                          onBlur={() => setFocusedField(null)}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              <div className={`input-group ${focusedField === 'email' ? 'focused' : ''}`}>
                <label htmlFor="email">E-mail</label>
                <div className="input-with-icon">
                  <Mail size={18} className="input-icon" />
                  <input 
                    id="email"
                    type="email" 
                    className="login-input" 
                    placeholder="seu@email.com" 
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setFocusedField('email')}
                    onBlur={() => setFocusedField(null)}
                  />
                </div>
              </div>

              <div className={`input-group ${focusedField === 'password' ? 'focused' : ''}`}>
                <label htmlFor="password">Senha</label>
                <div className="input-with-icon">
                  <Lock size={18} className="input-icon" />
                  <input 
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    className="login-input" 
                    placeholder="••••••••" 
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusedField('password')}
                    onBlur={() => setFocusedField(null)}
                  />
                  <button 
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {mode === 'signup' && (
                <div className={`input-group ${focusedField === 'confirm' ? 'focused' : ''}`}>
                  <label htmlFor="confirmPassword">Confirmar Senha</label>
                  <div className="input-with-icon">
                    <Lock size={18} className="input-icon" />
                    <input 
                      id="confirmPassword"
                      type={showPassword ? 'text' : 'password'}
                      className="login-input" 
                      placeholder="••••••••" 
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      onFocus={() => setFocusedField('confirm')}
                      onBlur={() => setFocusedField(null)}
                    />
                  </div>
                </div>
              )}
              
              {/* Status Messages */}
              {error && (
                <div className="auth-message error animate-slide-up">
                  <span className="msg-icon">✕</span>
                  {error}
                </div>
              )}
              {success && (
                <div className="auth-message success animate-slide-up">
                  <span className="msg-icon">✓</span>
                  {success}
                </div>
              )}

              <button type="submit" className="login-btn" disabled={loading} id="submit-auth">
                {loading ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    <span>Autenticando...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck size={20} />
                    <span>{mode === 'login' ? 'Acessar Biblioteca' : 'Criar Conta'}</span>
                    <ArrowRight size={16} className="btn-arrow" />
                  </>
                )}
              </button>

              <p className="auth-switch">
                {mode === 'login' ? 'Ainda não tem conta? ' : 'Já possui conta? '}
                <button 
                  type="button" 
                  className="switch-link"
                  onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
                >
                  {mode === 'login' ? 'Criar conta' : 'Entrar'}
                </button>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
