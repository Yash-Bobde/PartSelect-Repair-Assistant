import { useCallback, useEffect, useMemo, useState } from 'react';

// Legacy key: the shortlist used to be persisted here. We now keep it in memory
// only (see below), so purge any previously-saved list on load.
const LEGACY_STORAGE_KEY = 'partselect.shortlist';

// Parts the customer is collecting for this repair.
//
// Kept in memory only — NOT persisted. The rest of the repair (the chat, the
// backend conversation id, and the appliance/problem panel derived from the
// messages) is all ephemeral and resets on a page refresh, so the shortlist
// resets with it. Otherwise a refresh would show a stale parts list attached to
// a conversation that's already gone. Use "New repair" or just reload to clear.
export function useShortlist() {
  const [items, setItems] = useState([]);

  // One-time cleanup so a refresh no longer resurrects a previous repair's parts
  // from the old persisted list.
  useEffect(() => {
    try {
      window.localStorage.removeItem(LEGACY_STORAGE_KEY);
    } catch {
      // Storage can be unavailable (private mode) — nothing to clean up then.
    }
  }, []);

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
