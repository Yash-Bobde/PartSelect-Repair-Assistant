import { useCallback, useRef, useState } from 'react';
import { getAIMessage, resetConversation } from '../api/api';

let nextId = 0;
const newId = () => `m${(nextId += 1)}`;

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const busy = useRef(false);

  const ask = useCallback(async (text) => {
    busy.current = true;
    setLoading(true);
    const reply = await getAIMessage(text);
    setMessages((prev) => [...prev, { id: newId(), ...reply, retryText: reply.isError ? text : undefined }]);
    busy.current = false;
    setLoading(false);
  }, []);

  const send = useCallback(
    (text) => {
      const trimmed = (text || '').trim();
      if (!trimmed || busy.current) return false;
      setMessages((prev) => [...prev, { id: newId(), role: 'user', content: trimmed }]);
      ask(trimmed);
      return true;
    },
    [ask]
  );

  // Re-ask the question behind a failed reply, without repeating the user's bubble.
  const retry = useCallback(
    (failed) => {
      if (busy.current || !failed.retryText) return;
      setMessages((prev) => prev.filter((m) => m.id !== failed.id));
      ask(failed.retryText);
    },
    [ask]
  );

  const reset = useCallback(() => {
    resetConversation();
    setMessages([]);
  }, []);

  return { messages, loading, send, retry, reset };
}
