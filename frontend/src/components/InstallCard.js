import { useId, useState } from 'react';
import { motion } from 'framer-motion';
import { Play } from 'lucide-react';
import { useGuide } from '../hooks/useGuide';
import { formatPrice } from '../lib/parts';
import { Markdown } from './Markdown';
import { PartActions, PartRow, StockPill } from './PartCard';

const BEFORE_YOU_START = [
  'Unplug the appliance, and shut off the water if the part carries water',
  'Watch the video once all the way through',
  'Keep the old part to compare with the new one',
  'Test the appliance after you finish',
];

// Thumbnail first; the YouTube player only loads when the viewer asks for it.
function LiteYouTube({ id, title }) {
  const [playing, setPlaying] = useState(false);

  if (playing) {
    return (
      <div className="video">
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`}
          title={title}
          allow="autoplay; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }

  return (
    <button type="button" className="video video--poster" onClick={() => setPlaying(true)} aria-label={`Play: ${title}`}>
      <img src={`https://i.ytimg.com/vi/${id}/hqdefault.jpg`} alt="" loading="lazy" width="480" height="360" />
      <span className="video__play">
        <Play size={22} fill="currentColor" />
      </span>
    </button>
  );
}

function Checklist() {
  const baseId = useId();
  const [done, setDone] = useState(() => BEFORE_YOU_START.map(() => false));

  return (
    <fieldset className="checklist">
      <legend>Before you start</legend>
      {BEFORE_YOU_START.map((item, i) => (
        <label key={item} className="checklist__item" htmlFor={`${baseId}-${i}`}>
          <input
            id={`${baseId}-${i}`}
            type="checkbox"
            checked={done[i]}
            onChange={() => setDone((prev) => prev.map((v, j) => (j === i ? !v : v)))}
          />
          <span>{item}</span>
        </label>
      ))}
    </fieldset>
  );
}

// The guide's difficulty, time and tools are not shown: the scraper got "N/A"
// for both fields on every part, so the pipeline fills in defaults (moderate,
// 30 min, ["screwdriver"]). Only the install video is real data.
export function InstallCard({ part, fallback }) {
  const { status, videoId } = useGuide(part.partNumber);

  if (status === 'loading') {
    return (
      <div className="card install">
        <PartRow part={part} />
        <div className="video video--loading" aria-hidden="true" />
      </div>
    );
  }

  // No guide on file: show the part and the assistant's general steps.
  if (status === 'none') {
    return (
      <div className="card install">
        <PartRow part={part} />
        <Markdown text={fallback} className="install__fallback" />
        <PartActions part={part} showInstall={false} />
      </div>
    );
  }

  return (
    <motion.article
      className="card install"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.26, ease: [0.2, 0.8, 0.2, 1] }}
    >
      <header className="install__head">
        <div>
          <p className="eyebrow">Installation guide</p>
          <h3 className="install__title">{part.title}</h3>
          <p className="part-meta">
            {part.brand && <span>{part.brand}</span>}
            <span className="mono">{part.partNumber}</span>
          </p>
        </div>
        <div className="install__buy">
          <span className="price">{formatPrice(part.price)}</span>
          <StockPill inStock={part.inStock} />
        </div>
      </header>

      {videoId && <LiteYouTube id={videoId} title={`How to install ${part.title} (${part.partNumber})`} />}

      <Checklist />
      <PartActions part={part} showInstall={false} />
    </motion.article>
  );
}
