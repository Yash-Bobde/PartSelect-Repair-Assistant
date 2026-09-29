import { ClipboardList, Moon, RotateCcw, Sun } from 'lucide-react';

export function TopBar({ isDark, onToggleTheme, onOpenRepair, shortlistCount, onNewRepair, canReset }) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand__wordmark">PartSelect</span>
        <span className="brand__divider" aria-hidden="true" />
        <span className="brand__product">Repair Assistant</span>
      </div>

      <div className="topbar__actions">
        <button
          type="button"
          className="icon-btn"
          onClick={onToggleTheme}
          aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
          title={isDark ? 'Light theme' : 'Dark theme'}
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <button
          type="button"
          className="btn btn--ghost topbar__repair"
          onClick={onOpenRepair}
          aria-label={shortlistCount > 0 ? `Your repair, ${shortlistCount} parts in shortlist` : 'Your repair'}
        >
          <ClipboardList size={18} />
          <span className="hide-xs">Your repair</span>
          {shortlistCount > 0 && <span className="count-badge">{shortlistCount}</span>}
        </button>

        <button
          type="button"
          className="btn btn--outline"
          onClick={onNewRepair}
          disabled={!canReset}
          aria-label="Start a new repair"
        >
          <RotateCcw size={16} />
          <span className="hide-sm">New repair</span>
        </button>
      </div>
    </header>
  );
}
