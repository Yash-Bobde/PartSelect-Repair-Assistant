import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'partselect.theme';
const darkQuery = () => window.matchMedia?.('(prefers-color-scheme: dark)');

function savedTheme() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === 'light' || value === 'dark' ? value : null;
  } catch {
    return null;
  }
}

// null = follow the system setting; 'light' / 'dark' = the user's explicit choice.
export function useTheme() {
  const [theme, setTheme] = useState(savedTheme);
  const [systemDark, setSystemDark] = useState(() => Boolean(darkQuery()?.matches));

  useEffect(() => {
    const query = darkQuery();
    if (!query) return undefined;
    const onChange = (e) => setSystemDark(e.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme) root.setAttribute('data-theme', theme);
    else root.removeAttribute('data-theme');
    try {
      if (theme) window.localStorage.setItem(STORAGE_KEY, theme);
      else window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore unavailable storage.
    }
  }, [theme]);

  const isDark = theme ? theme === 'dark' : systemDark;
  const toggle = useCallback(() => setTheme(isDark ? 'light' : 'dark'), [isDark]);

  return { isDark, toggle };
}
