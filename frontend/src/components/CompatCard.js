import { motion } from 'framer-motion';
import { CircleCheck, CircleHelp, ShieldCheck } from 'lucide-react';
import { PartActions, PartRow } from './PartCard';

// Wording follows the backend's reasons for each verdict
// (see _check_detailed_compatibility in partselect-backend/app/agent/nodes.py).
function describe(verdict, part, model) {
  if (verdict.kind === 'yes' && verdict.pair) {
    return {
      tone: 'yes',
      icon: CircleCheck,
      title: `${verdict.pair[0]} and ${verdict.pair[1]} are interchangeable`,
      body: 'These part numbers are listed as replacements for each other.',
    };
  }
  if (verdict.kind === 'yes') {
    return {
      tone: 'yes',
      icon: CircleCheck,
      title: `Fits your ${model}`,
      body: 'Your model number appears in this part’s compatibility data.',
    };
  }
  if (verdict.kind === 'likely') {
    const brand = part.brand ? `${part.brand} ` : '';
    return {
      tone: 'likely',
      icon: ShieldCheck,
      title: `Likely fits your ${model}`,
      body: `This ${brand}part fits many models in the same brand family. Confirm your model on the product page before ordering.`,
    };
  }
  return {
    tone: 'unknown',
    icon: CircleHelp,
    title: `Can’t confirm a fit for ${model}`,
    body: 'The catalog has no compatibility record for this pair. That doesn’t mean it won’t fit: check the model list on the product page, or ask the manufacturer.',
  };
}

export function CompatCard({ verdict, part, model }) {
  const v = describe(verdict, part, model || 'model');
  const Icon = v.icon;

  return (
    <motion.article
      className={`card compat compat--${v.tone}`}
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.24, ease: [0.2, 0.8, 0.2, 1] }}
    >
      <div className="compat__verdict" role="status">
        <span className="compat__icon">
          <Icon size={28} />
        </span>
        <div>
          <p className="compat__title">{v.title}</p>
          <p className="compat__body">{v.body}</p>
        </div>
      </div>
      <PartRow part={part} />
      <PartActions part={part} showFit={false} />
    </motion.article>
  );
}
