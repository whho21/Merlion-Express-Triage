import { useSyncExternalStore } from 'react';
import AppShell from './layouts/AppShell.jsx';
import TriagePage from './pages/TriagePage.jsx';
import WeeklyPage from './pages/WeeklyPage.jsx';
import HowItWorksPage from './pages/HowItWorksPage.jsx';
import { TriageProvider } from './contexts/TriageContext.jsx';

// Minimal hash routing (#/triage, #/weekly, #/how-it-works).
// Lesson 2.8 uses react-router; swap to <BrowserRouter> once it is added to package.json.
// Hash URLs also work with no server rewrite rules (Lesson 2.11's _redirects problem).
function subscribe(callback) {
  window.addEventListener('hashchange', callback);
  return () => window.removeEventListener('hashchange', callback);
}
const getPath = () => window.location.hash.replace(/^#/, '') || '/triage';

function renderPage(path) {
  switch (path) {
    case '/triage':
      return <TriagePage />;
    case '/weekly':
      return <WeeklyPage />;
    case '/how-it-works':
      return <HowItWorksPage />;
    default:
      return <NotFound />;
  }
}

function NotFound() {
  return (
    <div>
      <h1>Page not found</h1>
      <a href="#/triage">Back to triage</a>
    </div>
  );
}

export default function App() {
  const path = useSyncExternalStore(subscribe, getPath);
  return (
    <TriageProvider>
      <AppShell current={path}>
        {renderPage(path)}
      </AppShell>
    </TriageProvider>
  );
}
