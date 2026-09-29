import { useEffect, useId, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Check, ClipboardList, Copy, ExternalLink, Info, Stethoscope, Trash2, X } from 'lucide-react';
import { capitalize, formatPrice } from '../lib/parts';
import { ModelHelp } from './FollowUps';
import { ApplianceIcon } from './Icons';

function Unknown({ children = 'Not known yet' }) {
  return <span className="placeholder">{children}</span>;
}

export function RepairPanel({ context, problems, shortlist, onAddModel, onClose }) {
  const id = useId(); // the panel renders twice (docked + drawer), so ids must be unique
  const [copied, setCopied] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  useEffect(() => {
    if (!copied) return undefined;
    const t = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(t);
  }, [copied]);

  const copyList = async () => {
    const lines = shortlist.items.map((p) => `${p.partNumber}  ${p.title}  ${formatPrice(p.price)}`);
    lines.push(`Total: ${formatPrice(shortlist.total)}`);
    const text = lines.join('\n');

    let ok = false;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        ok = true;
      }
    } catch {
      ok = false;
    }

    // Fallback for contexts where the async Clipboard API is blocked/unavailable.
    if (!ok) {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        ok = document.execCommand('copy');
        document.body.removeChild(ta);
      } catch {
        ok = false;
      }
    }

    if (ok) setCopied(true);
  };

  return (
    <div className="repair">
      <div className="repair__head">
        <div>
          <h2 className="repair__title">Your repair</h2>
          <p className="repair__sub">Fills in as you chat</p>
        </div>
        {onClose && (
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close your repair" data-autofocus>
            <X size={18} />
          </button>
        )}
      </div>

      <section className="repair__section" aria-labelledby={`${id}-appliance`}>
        <h3 id={`${id}-appliance`} className="repair__label">
          Appliance
        </h3>
        <div className="appliance-card">
          <span className={`appliance-card__icon${context.appliance ? ' appliance-card__icon--active' : ''}`}>
            <ApplianceIcon type={context.appliance} size={26} strokeWidth={1.75} />
          </span>
          <dl className="appliance-card__facts">
            <div>
              <dt>Type</dt>
              <dd>{context.appliance ? capitalize(context.appliance) : <Unknown />}</dd>
            </div>
            <div>
              <dt>Brand</dt>
              <dd>{context.brand || <Unknown />}</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>
                {context.model ? (
                  <span className="mono">{context.model}</span>
                ) : (
                  <button type="button" className="link-btn" onClick={onAddModel}>
                    Add model number
                  </button>
                )}
              </dd>
            </div>
          </dl>
        </div>
        {!context.model && (
          <button
            type="button"
            className="link-btn link-btn--muted"
            onClick={() => setHelpOpen((v) => !v)}
            aria-expanded={helpOpen}
          >
            Where do I find it?
          </button>
        )}
        {helpOpen && !context.model && <ModelHelp />}
      </section>

      <section className="repair__section" aria-labelledby={`${id}-problem`}>
        <h3 id={`${id}-problem`} className="repair__label">
          Reported problem
        </h3>
        {problems.length ? (
          <ul className="problems">
            {problems.map((p) => (
              <li key={p}>
                <Stethoscope size={16} />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty">Describe a symptom and it will show up here.</p>
        )}
      </section>

      <section className="repair__section repair__section--grow" aria-labelledby={`${id}-parts`}>
        <h3 id={`${id}-parts`} className="repair__label">
          Parts shortlist
          {shortlist.items.length > 0 && <span className="count-badge">{shortlist.items.length}</span>}
        </h3>

        {shortlist.items.length === 0 ? (
          <div className="empty empty--box">
            <ClipboardList size={22} />
            <p>Add parts from the chat to build your order.</p>
          </div>
        ) : (
          <>
            <ul className="shortlist">
              <AnimatePresence initial={false}>
                {shortlist.items.map((p) => (
                  <motion.li
                    key={p.partNumber}
                    layout
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 12, transition: { duration: 0.15 } }}
                    className="shortlist__item"
                  >
                    <div className="shortlist__main">
                      {p.url ? (
                        <a href={p.url} target="_blank" rel="noopener noreferrer" className="shortlist__title">
                          {p.title}
                          <ExternalLink size={12} />
                          <span className="sr-only">(opens in a new tab)</span>
                        </a>
                      ) : (
                        <span className="shortlist__title">{p.title}</span>
                      )}
                      <span className="mono shortlist__pn">{p.partNumber}</span>
                    </div>
                    <span className="shortlist__price">{formatPrice(p.price)}</span>
                    <button
                      type="button"
                      className="icon-btn icon-btn--sm"
                      onClick={() => shortlist.remove(p.partNumber)}
                      aria-label={`Remove ${p.title} from your repair`}
                    >
                      <Trash2 size={15} />
                    </button>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
            <div className="shortlist__total">
              <span>Total</span>
              <span>{formatPrice(shortlist.total)}</span>
            </div>
            <div className="shortlist__actions">
              <button type="button" className="btn btn--primary" onClick={copyList}>
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? 'Copied' : 'Copy parts list'}
              </button>
              <button type="button" className="btn btn--ghost" onClick={shortlist.clear}>
                Clear
              </button>
            </div>
          </>
        )}
      </section>

      <p className="repair__foot">
        <Info size={14} />
        The assistant remembers this conversation for 24 hours.
      </p>
    </div>
  );
}
