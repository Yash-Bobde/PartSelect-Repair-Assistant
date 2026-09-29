import { forwardRef, useLayoutEffect } from 'react';
import { ArrowUp } from 'lucide-react';

const MAX_HEIGHT = 160;

export const Composer = forwardRef(function Composer({ value, onChange, onSend, loading, placeholder }, ref) {
  // Grow with the text, up to a few lines.
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  }, [value, ref]);

  const submit = (e) => {
    e.preventDefault();
    onSend();
  };

  return (
    <form className="composer" onSubmit={submit}>
      <label htmlFor="composer-input" className="sr-only">
        Message the repair assistant
      </label>
      <div className="composer__box">
        <textarea
          id="composer-input"
          ref={ref}
          rows={1}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) submit(e);
          }}
        />
        <button type="submit" className="send-btn" disabled={loading || !value.trim()} aria-label="Send message">
          <ArrowUp size={20} />
        </button>
      </div>
      <p className="composer__hint">
        <span>Refrigerator &amp; dishwasher parts only</span>
        <span className="hide-sm">Enter to send · Shift + Enter for a new line</span>
      </p>
    </form>
  );
});
