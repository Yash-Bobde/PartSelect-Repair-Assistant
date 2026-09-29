import { useCallback, useMemo, useState } from 'react';

// Parts the customer is collecting for this repair. Kept in memory only, so a
// page refresh clears the shortlist together with the chat — the whole "Your
// repair" workspace resets to a clean slate rather than leaving a stale cart.
export function useShortlist() {
  const [items, setItems] = useState([]);

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
