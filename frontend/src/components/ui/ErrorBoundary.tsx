import React from 'react';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          height: '100vh', padding: '2rem', textAlign: 'center', color: '#e0e0e0',
          background: 'linear-gradient(135deg, #0a0e1a 0%, #111827 100%)',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠</div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            Algo deu errado
          </h1>
          <p style={{ color: '#94a3b8', maxWidth: 400, marginBottom: '1.5rem' }}>
            Ocorreu um erro inesperado. A sessão não foi afetada — tente recarregar a página.
          </p>
          <button onClick={this.handleReset}
            style={{
              padding: '0.75rem 2rem', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: '#c9a96e', color: '#0a0e1a', fontWeight: 600, fontSize: '0.9rem',
            }}
          >
            Tentar novamente
          </button>
          {this.state.error && (
            <details style={{ marginTop: '1.5rem', opacity: 0.5, fontSize: '0.8rem', maxWidth: 500 }}>
              <summary>Detalhes técnicos</summary>
              <pre style={{ whiteSpace: 'pre-wrap', marginTop: '0.5rem' }}>
                {this.state.error.message}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
