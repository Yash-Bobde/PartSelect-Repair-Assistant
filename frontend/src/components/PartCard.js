import { motion } from 'framer-motion';
import { Check, ExternalLink, PackageCheck, PackageX, Play, Plus, ShieldCheck, Wrench } from 'lucide-react';
import { useChatActions } from '../context/ChatActions';
import { useGuide } from '../hooks/useGuide';
import { formatPrice } from '../lib/parts';
import { ApplianceIcon } from './Icons';

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.26, ease: [0.2, 0.8, 0.2, 1] } },
};

export function StockPill({ inStock }) {
  return (
    <span className={`stock ${inStock ? 'stock--in' : 'stock--out'}`}>
      {inStock ? <PackageCheck size={14} /> : <PackageX size={14} />}
      {inStock ? 'In stock' : 'Out of stock'}
    </span>
  );
}

// Thumbnail from the part's YouTube install video (the catalog has no product photos).
export function VideoThumb({ part }) {
  const { openVideo } = useChatActions();
  const { status, videoId } = useGuide(part.partNumber);

  if (status === 'loading') return <div className="thumb thumb--loading" aria-hidden="true" />;

  if (!videoId) {
    return (
      <div className="thumb thumb--empty">
        <ApplianceIcon type={part.category} size={30} strokeWidth={1.5} />
        <span>No install video</span>
      </div>
    );
  }

  return (
    <button
      type="button"
      className="thumb"
      onClick={() => openVideo({ id: videoId, title: `How to install ${part.title} (${part.partNumber})` })}
      aria-label={`Play the install video for ${part.title}`}
    >
      <img src={`https://i.ytimg.com/vi/${videoId}/mqdefault.jpg`} alt="" loading="lazy" width="320" height="180" />
      <span className="thumb__play">
        <Play size={16} fill="currentColor" />
      </span>
      <span className="thumb__label">Install video</span>
    </button>
  );
}

export function PartActions({ part, compact = false, showInstall = true, showFit = true }) {
  const { send, prefill, shortlist, context, loading } = useChatActions();
  const added = shortlist.has(part.partNumber);

  const checkFit = () =>
    context.model
      ? send(`Is ${part.partNumber} compatible with ${context.model}?`)
      : prefill(`Is ${part.partNumber} compatible with my model `);

  return (
    <div className={`part-actions${compact ? ' part-actions--compact' : ''}`}>
      <button
        type="button"
        className={`btn ${added ? 'btn--added' : 'btn--primary'}`}
        aria-pressed={added}
        onClick={() => shortlist.toggle(part)}
      >
        {added ? <Check size={16} /> : <Plus size={16} />}
        {added ? 'In your repair' : 'Add to repair'}
      </button>
      <div className="part-actions__row">
        {showInstall && (
          <button
            type="button"
            className="btn btn--soft"
            onClick={() => send(`How do I install ${part.partNumber}?`)}
            disabled={loading}
          >
            <Wrench size={16} />
            Install
          </button>
        )}
        {showFit && (
          <button type="button" className="btn btn--soft" onClick={checkFit} disabled={loading}>
            <ShieldCheck size={16} />
            Check fit
          </button>
        )}
        {part.url && (
          <a
            className="btn btn--soft btn--icon"
            href={part.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`View ${part.title} on PartSelect (opens in a new tab)`}
            title="View on PartSelect"
          >
            <ExternalLink size={16} />
          </a>
        )}
      </div>
    </div>
  );
}

export function PartCard({ part }) {
  const extraFixes = part.fixes.length - 2;
  return (
    <motion.article className="part-card" variants={cardVariants}>
      <VideoThumb part={part} />
      <div className="part-card__body">
        <h3 className="part-card__title" title={part.name}>
          {part.title}
        </h3>
        <p className="part-meta">
          {part.brand && <span>{part.brand}</span>}
          <span className="mono">{part.partNumber}</span>
        </p>
        <div className="part-card__buy">
          <span className="price">{formatPrice(part.price)}</span>
          <StockPill inStock={part.inStock} />
        </div>
        {part.fixes.length > 0 && (
          <div className="fixes">
            <span className="fixes__label">Fixes</span>
            <ul className="tag-list">
              {part.fixes.slice(0, 2).map((fix) => (
                <li key={fix} className="tag">
                  {fix}
                </li>
              ))}
              {extraFixes > 0 && <li className="tag tag--more">+{extraFixes} more</li>}
            </ul>
          </div>
        )}
      </div>
      <PartActions part={part} compact />
    </motion.article>
  );
}

export function PartGrid({ parts }) {
  return (
    <motion.div
      className="part-grid"
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.07 } } }}
    >
      {parts.map((part) => (
        <PartCard key={part.partNumber} part={part} />
      ))}
    </motion.div>
  );
}

// One-line summary of a part, used inside verdict and guide cards.
export function PartRow({ part }) {
  return (
    <div className="part-row">
      <span className="part-row__icon">
        <ApplianceIcon type={part.category} size={20} />
      </span>
      <div className="part-row__main">
        <span className="part-row__title">{part.title}</span>
        <span className="part-meta">
          {part.brand && <span>{part.brand}</span>}
          <span className="mono">{part.partNumber}</span>
        </span>
      </div>
      <div className="part-row__buy">
        <span className="price price--sm">{formatPrice(part.price)}</span>
        <StockPill inStock={part.inStock} />
      </div>
    </div>
  );
}
