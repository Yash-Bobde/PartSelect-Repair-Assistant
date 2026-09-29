import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { RotateCcw, TriangleAlert, Wrench } from 'lucide-react';
import { useChatActions } from '../context/ChatActions';
import { normalizePart } from '../lib/parts';
import { compatVerdict, intentInfo, introText } from '../lib/replies';
import { AgentTrace } from './AgentTrace';
import { CompatCard } from './CompatCard';
import { FollowUps } from './FollowUps';
import { InstallCard } from './InstallCard';
import { Markdown } from './Markdown';
import { PartGrid } from './PartCard';
import { PartDetail } from './PartDetail';

const enter = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.22, ease: [0.2, 0.8, 0.2, 1] },
};

function Avatar() {
  return (
    <span className="avatar" aria-hidden="true">
      <Wrench size={16} />
    </span>
  );
}

// Pick the richest view for each kind of answer; fall back to the text reply.
function ReplyBody({ message, parts }) {
  const top = parts[0];

  switch (message.intent) {
    case 'search_part':
    case 'diagnose_issue':
      if (parts.length) {
        return (
          <>
            <Markdown text={introText(message.content) || 'Here are the best matches from the catalog.'} />
            <PartGrid parts={parts} />
          </>
        );
      }
      break;
    case 'product_details':
      if (top) return <PartDetail part={top} />;
      break;
    case 'installation_help':
      if (top) return <InstallCard part={top} fallback={message.content} />;
      break;
    case 'compatibility_check': {
      const verdict = compatVerdict(message.content);
      if (verdict && top) return <CompatCard verdict={verdict} part={top} model={message.metadata?.model_number} />;
      break;
    }
    default:
      break;
  }
  return <Markdown text={message.content} />;
}

function AssistantMessage({ message, isLatest }) {
  const { retry, loading } = useChatActions();
  const parts = useMemo(() => (message.recommendedParts || []).map(normalizePart), [message.recommendedParts]);
  const intent = intentInfo(message.intent);

  if (message.isError) {
    return (
      <motion.div className="msg msg--assistant" {...enter}>
        <Avatar />
        <div className="msg__body">
          <div className="error-card" role="alert">
            <TriangleAlert size={18} />
            <p>{message.content}</p>
            <button type="button" className="btn btn--outline btn--sm" onClick={() => retry(message)} disabled={loading}>
              <RotateCcw size={14} />
              Try again
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div className="msg msg--assistant" {...enter}>
      <Avatar />
      <div className="msg__body">
        <div className="msg__meta">
          <span className="msg__name">Repair Assistant</span>
          <span className="intent-tag">
            <intent.icon size={13} />
            {intent.label}
          </span>
        </div>
        <ReplyBody message={message} parts={parts} />
        {isLatest && <FollowUps message={message} parts={parts} />}
        <AgentTrace message={message} parts={parts} />
      </div>
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <motion.div className="msg msg--assistant" {...enter}>
      <Avatar />
      <div className="msg__body">
        <div className="typing" role="status">
          <span className="typing__dots" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span className="typing__label">Working on it…</span>
        </div>
      </div>
    </motion.div>
  );
}

export function MessageList({ messages, loading }) {
  const lastId = messages[messages.length - 1]?.id;

  return (
    <div className="messages" role="log" aria-label="Conversation" aria-live="polite">
      {messages.map((message) =>
        message.role === 'user' ? (
          <motion.div key={message.id} className="msg msg--user" {...enter}>
            <p className="bubble">{message.content}</p>
          </motion.div>
        ) : (
          <AssistantMessage key={message.id} message={message} isLatest={message.id === lastId && !loading} />
        )
      )}
      {loading && <TypingIndicator />}
    </div>
  );
}
