import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useChatActions } from '../context/ChatActions';
import { buildFollowUps } from '../lib/replies';

export function ModelHelp() {
  return (
    <div className="model-help">
      <p className="model-help__title">Finding your model number</p>
      <ul>
        <li>
          <strong>Refrigerator:</strong> a sticker inside the fresh-food section, usually on a side wall or the ceiling.
        </li>
        <li>
          <strong>Dishwasher:</strong> a sticker on the edge of the door or the tub frame. Open the door to see it.
        </li>
      </ul>
      <p className="model-help__note">
        It looks like <span className="mono">WDT780SAEM1</span> or <span className="mono">WRS325SDHZ</span>, and is
        different from the serial number.
      </p>
    </div>
  );
}

export function FollowUps({ message, parts }) {
  const { send, loading } = useChatActions();
  const [helpOpen, setHelpOpen] = useState(false);
  const chips = buildFollowUps(message, parts);

  if (!chips.length) return null;

  const run = (chip) => {
    if (chip.kind === 'send') send(chip.text);
    else setHelpOpen((v) => !v);
  };

  return (
    <div className="followups">
      <div className="followups__row" role="group" aria-label="Suggested next steps">
        {chips.map((chip) => (
          <button
            key={chip.label}
            type="button"
            className="chip-btn"
            onClick={() => run(chip)}
            disabled={chip.kind === 'send' && loading}
            aria-expanded={chip.kind === 'help' ? helpOpen : undefined}
          >
            <chip.icon size={15} />
            {chip.label}
          </button>
        ))}
      </div>
      <AnimatePresence initial={false}>
        {helpOpen && (
          <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <ModelHelp />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
