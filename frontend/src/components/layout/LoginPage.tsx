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
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const carouselImages = [
    '/dehon_1.jpg',
    '/dehon_2.jpg',
    '/dehon_3.jpg'
  ];

  // Carousel auto-rotate timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % carouselImages.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  // Clear messages on mode switch
  useEffect(() => {
    setError(null);
    setSuccess(null);
  }, [mode]);

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

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin
        }
      });
      if (error) throw error;
    } catch (err: any) {
      setError(err.message || 'Erro ao autenticar com o Google.');
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
        {/* Left: Brand Panel with Carousel */}
        <div className="login-brand-panel">
          <div className="login-carousel">
            {carouselImages.map((img, idx) => (
              <div
                key={idx}
                className={`login-carousel-slide ${idx === currentImageIndex ? 'active' : ''}`}
                style={{ backgroundImage: `url(${img})` }}
              />
            ))}
            <div className="login-carousel-overlay" />
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
                    <span>{mode === 'login' ? 'Acessar Biblioteca' : 'Criar Conta'}</span>
                    <ArrowRight size={16} className="btn-arrow" />
                  </>
                )}
              </button>

              <div className="auth-divider">
                <span>ou</span>
              </div>

              <button 
                type="button" 
                className="google-btn" 
                onClick={handleGoogleLogin} 
                disabled={loading}
              >
                <svg className="google-icon" viewBox="0 0 24 24" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
                </svg>
                <span>Entrar com o Google</span>
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
