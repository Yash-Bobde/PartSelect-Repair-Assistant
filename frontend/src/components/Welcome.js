import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, BookOpen, ShieldCheck, Stethoscope, Wrench, Search } from 'lucide-react';
import { ApplianceIcon } from './Icons';

const APPLIANCES = [
  { id: 'refrigerator', label: 'Refrigerator' },
  { id: 'dishwasher', label: 'Dishwasher' },
];

// The first two refrigerator prompts and the dishwasher compatibility prompt
// are the example questions from the case-study brief.
const STARTERS = {
  refrigerator: [
    { kind: 'Diagnose', icon: Stethoscope, text: 'The ice maker on my Whirlpool fridge is not working. How can I fix it?' },
    { kind: 'Install', icon: Wrench, text: 'How can I install part number PS11752778?' },
    { kind: 'Find a part', icon: Search, text: 'I need a water filter for my Whirlpool refrigerator' },
  ],
  dishwasher: [
    { kind: 'Compatibility', icon: ShieldCheck, text: 'Is PS11759673 compatible with my WDT780SAEM1 model?' },
    { kind: 'Diagnose', icon: Stethoscope, text: 'My dishwasher is not draining' },
    { kind: 'Find a part', icon: Search, text: 'Show me dishwasher spray arms' },
  ],
};

const CAPABILITIES = [
  { icon: Stethoscope, label: 'Diagnose symptoms' },
  { icon: ShieldCheck, label: 'Check fit by model' },
  { icon: BookOpen, label: 'Install videos' },
];

const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };

const rise = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.2, 0.8, 0.2, 1] } },
};

export function Welcome({ onAsk }) {
  const [appliance, setAppliance] = useState('refrigerator');

  return (
    <motion.section
      className="welcome"
      aria-labelledby="welcome-title"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      <motion.p className="eyebrow" variants={rise}>
        Refrigerator &amp; dishwasher parts
      </motion.p>
      <motion.h1 id="welcome-title" className="welcome__title" variants={rise}>
        What are you fixing today?
      </motion.h1>
      <motion.p className="welcome__sub" variants={rise}>
        Describe what's wrong, paste a part number, or check whether a part fits your model. Answers come from the
        PartSelect catalog.
      </motion.p>

      <motion.div className="appliance-picker" variants={rise} role="group" aria-label="Choose an appliance">
        {APPLIANCES.map((a) => (
          <button
            key={a.id}
            type="button"
            className="appliance-tile"
            aria-pressed={appliance === a.id}
            onClick={() => setAppliance(a.id)}
          >
            <span className="appliance-tile__icon">
              <ApplianceIcon type={a.id} size={28} strokeWidth={1.75} />
            </span>
            <span className="appliance-tile__label">{a.label}</span>
          </button>
        ))}
      </motion.div>

      <motion.div className="starters" variants={rise}>
        <p className="starters__label">Try asking</p>
        <ul className="starters__list">
          {STARTERS[appliance].map((s) => (
            <li key={s.text}>
              <button type="button" className="starter" onClick={() => onAsk(s.text)}>
                <span className="starter__icon">
                  <s.icon size={18} />
                </span>
                <span className="starter__text">
                  <span className="starter__kind">{s.kind}</span>
                  <span>{s.text}</span>
                </span>
                <ArrowRight size={18} className="starter__go" />
              </button>
            </li>
          ))}
        </ul>
      </motion.div>

      <motion.ul className="capabilities" variants={rise} aria-label="What the assistant can do">
        {CAPABILITIES.map((c) => (
          <li key={c.label}>
            <c.icon size={16} />
            {c.label}
          </li>
        ))}
      </motion.ul>
    </motion.section>
  );
}
