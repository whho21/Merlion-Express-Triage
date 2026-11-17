// Context object and consumer hook kept outside the Provider file so
// eslint-plugin-react-refresh (only-export-components) stays happy.
import { createContext, useContext } from 'react';

export const TriageContext = createContext(null);

// Lesson 2.6 Challenge 1: helper hook with an error guard.
export function useTriage() {
  const ctx = useContext(TriageContext);
  if (!ctx) throw new Error('useTriage must be used inside <TriageProvider>');
  return ctx;
}
