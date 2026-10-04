import { motion } from 'framer-motion';
import { capitalize, formatPrice } from '../lib/parts';
import { PartActions, StockPill, VideoThumb } from './PartCard';

const SHOWN_REPLACES = 8;

export function PartDetail({ part }) {
  const moreReplaces = part.replaces.length - SHOWN_REPLACES;

  return (
    <motion.article
      className="card detail"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.26, ease: [0.2, 0.8, 0.2, 1] }}
    >
      <div className="detail__media">
        <VideoThumb part={part} />
        {part.replaces.length > 0 && (
          <section className="detail__section">
            <h4>Also replaces</h4>
            <p className="replaces mono">
              {part.replaces.slice(0, SHOWN_REPLACES).join(', ')}
              {moreReplaces > 0 && <span className="replaces__more"> +{moreReplaces} more</span>}
            </p>
          </section>
        )}
      </div>

      <div className="detail__main">
        {part.category && <p className="eyebrow">{capitalize(part.category)} part</p>}
        <h3 className="detail__title">{part.title}</h3>
        <p className="part-meta">
          {part.brand && <span>{part.brand}</span>}
          <span className="mono">{part.partNumber}</span>
          {part.mpn && <span className="mono">MPN {part.mpn}</span>}
        </p>

        <div className="detail__buy">
          <span className="price price--lg">{formatPrice(part.price)}</span>
          <StockPill inStock={part.inStock} />
        </div>

        {part.fixes.length > 0 && (
          <section className="detail__section">
            <h4>Fixes these problems</h4>
            <ul className="tag-list">
              {part.fixes.map((fix) => (
                <li key={fix} className="tag">
                  {fix}
                </li>
              ))}
            </ul>
          </section>
        )}

        <PartActions part={part} />
      </div>
    </motion.article>
  );
}
