import { useCallback, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'partselect.shortlist';

function load() {
  try {
    const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY));
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

// Parts the customer is collecting for this repair. Kept in localStorage so a
// page refresh doesn't lose them.
export function useShortlist() {
  const [items, setItems] = useState(load);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // Storage can be unavailable (private mode); the list still works in memory.
    }
  }, [items]);

  const has = useCallback((partNumber) => items.some((p) => p.partNumber === partNumber), [items]);

  const toggle = useCallback((part) => {
    setItems((prev) =>
      prev.some((p) => p.partNumber === part.partNumber)
        ? prev.filter((p) => p.partNumber !== part.partNumber)
        : [...prev, part]
    );
  }, []);

  const remove = useCallback((partNumber) => {
    setItems((prev) => prev.filter((p) => p.partNumber !== partNumber));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  const total = useMemo(() => items.reduce((sum, p) => sum + (Number.isFinite(p.price) ? p.price : 0), 0), [items]);

  return { items, has, toggle, remove, clear, total };
}
