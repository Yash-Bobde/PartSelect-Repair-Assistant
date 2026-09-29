import { useEffect, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';

// Close on Escape, move focus into the overlay, and hand it back on close.
function useDialog(open, onClose, ref) {
  useEffect(() => {
    if (!open) return undefined;
    const previous = document.activeElement;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    const target = ref.current?.querySelector('[data-autofocus]') || ref.current;
    target?.focus();
    return () => {
      document.removeEventListener('keydown', onKey);
      previous?.focus?.();
    };
  }, [open, onClose, ref]);
}

export function Drawer({ open, onClose, label, children }) {
  const ref = useRef(null);
  useDialog(open, onClose, ref);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="backdrop"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          <motion.aside
            ref={ref}
            className="drawer"
            role="dialog"
            aria-modal="true"
            aria-label={label}
            tabIndex={-1}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%', transition: { duration: 0.18 } }}
            transition={{ type: 'tween', duration: 0.24, ease: [0.2, 0.8, 0.2, 1] }}
          >
            {children}
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

export function VideoModal({ video, onClose }) {
  const ref = useRef(null);
  useDialog(Boolean(video), onClose, ref);

  return (
    <AnimatePresence>
      {video && (
        <>
          <motion.div
            className="backdrop backdrop--dark"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
          <motion.div
            ref={ref}
            className="video-modal"
            role="dialog"
            aria-modal="true"
            aria-label={video.title}
            tabIndex={-1}
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98, transition: { duration: 0.12 } }}
            transition={{ duration: 0.2 }}
          >
            <div className="video-modal__head">
              <p>{video.title}</p>
              <button type="button" className="icon-btn icon-btn--light" onClick={onClose} aria-label="Close video" data-autofocus>
                <X size={18} />
              </button>
            </div>
            <div className="video">
              <iframe
                src={`https://www.youtube-nocookie.com/embed/${video.id}?autoplay=1&rel=0`}
                title={video.title}
                allow="autoplay; encrypted-media; picture-in-picture"
                allowFullScreen
              />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
