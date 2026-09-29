import { Fragment, useId, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, ChevronRight, Workflow } from 'lucide-react';
import { PIPELINE, buildTrace } from '../lib/replies';

// "How I answered": the LangGraph path this reply took and what the agent understood.
export function AgentTrace({ message, parts }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const { ran, steps } = useMemo(() => buildTrace(message, parts), [message, parts]);

  return (
    <div className="trace">
      <button
        type="button"
        className="trace__toggle"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
      >
        <Workflow size={15} />
        How I answered
        <ChevronDown size={15} className={`trace__chevron${open ? ' is-open' : ''}`} />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={panelId}
            className="trace__panel"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4, transition: { duration: 0.12 } }}
            transition={{ duration: 0.18 }}
          >
            <ol className="pipeline" aria-label="Agent pipeline">
              {PIPELINE.map((node, i) => (
                <Fragment key={node}>
                  {i > 0 && (
                    <li className="pipeline__arrow" aria-hidden="true">
                      <ChevronRight size={14} />
                    </li>
                  )}
                  <li className={`pipeline__node${ran.has(node) ? ' is-on' : ''}`}>
                    {node}
                    <span className="sr-only">{ran.has(node) ? ' (ran)' : ' (skipped)'}</span>
                  </li>
                </Fragment>
              ))}
            </ol>

            <ol className="trace__steps">
              {steps.map((step) => (
                <li key={step.node} className="trace__step">
                  <span className="trace__dot" aria-hidden="true" />
                  <div>
                    <p className="trace__title">{step.title}</p>
                    <p className="trace__detail">{step.detail}</p>
                    {step.facts?.length > 0 && (
                      <ul className="trace__facts">
                        {step.facts.map((f) => (
                          <li key={f.label}>
                            <span className="trace__fact-label">{f.label}</span>
                            <span className={f.mono ? 'mono' : undefined}>{f.value}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
