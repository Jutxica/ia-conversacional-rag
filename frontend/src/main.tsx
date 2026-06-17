import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import ErrorBoundary from './components/ui/ErrorBoundary'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App isAdmin={false} onSwitchToAdmin={() => {}} />
    </ErrorBoundary>
  </StrictMode>,
)
