// Reads the assistant's replies: which intent they answered, what the agent
// did, what to suggest next, and what the conversation has established so far.
import { CircleHelp, Info, MessageSquare, Search, ShieldCheck, Stethoscope, Wrench } from 'lucide-react';
import { capitalize } from './parts';

export const INTENTS = {
  search_part: { label: 'Find a part', icon: Search },
  diagnose_issue: { label: 'Diagnose a problem', icon: Stethoscope },
  compatibility_check: { label: 'Check compatibility', icon: ShieldCheck },
  installation_help: { label: 'Installation help', icon: Wrench },
  product_details: { label: 'Part details', icon: Info },
  general_question: { label: 'General question', icon: MessageSquare },
};

export const intentInfo = (intent) => INTENTS[intent] || INTENTS.general_question;

// Mirrors the routing in partselect-backend/app/agent/graph.py.
export const PIPELINE = ['understand', 'search', 'gather_context', 'recommend', 'respond'];
const SEARCH_INTENTS = ['search_part', 'diagnose_issue', 'installation_help', 'compatibility_check', 'product_details'];
const CONTEXT_INTENTS = ['diagnose_issue', 'installation_help'];

// Search and diagnosis replies end in a text list of the same parts we render
// as cards; keep only the introduction above that list.
const LIST_MARKERS = ['**Recommended parts:**', 'Here are the parts I found:'];

export function introText(content = '') {
  for (const marker of LIST_MARKERS) {
    const index = content.indexOf(marker);
    if (index >= 0) return content.slice(0, index).trim();
  }
  return content;
}

// Compatibility replies come from fixed templates in the backend; map each to a verdict.
export function compatVerdict(content = '') {
  const pair = content.match(/Yes, (\S+) and (\S+) are compatible/);
  if (pair) return { kind: 'yes', pair: [pair[1], pair[2]] };
  if (content.includes('should be compatible')) return { kind: 'likely' };
  if (content.includes('Yes, this part is compatible')) return { kind: 'yes' };
  const other = content.match(/This is a (\w+) part, and \S+ looks like a (\w+) model/);
  if (content.includes('is not compatible with your')) return { kind: 'no', partType: other?.[1], modelType: other?.[2] };
  if (content.includes("couldn't confirm compatibility")) return { kind: 'unknown' };
  return null;
}

export function buildTrace(message, parts) {
  const intent = message.intent || 'general_question';
  const meta = message.metadata || {};
  const ran = new Set(['understand']);
  const steps = [];

  const confidence = typeof meta.confidence === 'number' ? ` · ${Math.round(meta.confidence * 100)}% confident` : '';
  const facts = [
    meta.appliance_type && { label: 'Appliance', value: capitalize(meta.appliance_type) },
    meta.brand && { label: 'Brand', value: meta.brand },
    meta.model_number && { label: 'Model', value: meta.model_number, mono: true },
  ].filter(Boolean);

  steps.push({
    node: 'understand',
    title: 'Understood the question',
    detail: `${intentInfo(intent).label}${confidence}`,
    facts,
  });

  if (!SEARCH_INTENTS.includes(intent)) {
    ran.add('respond');
    steps.push({
      node: 'respond',
      title: 'Answered directly',
      detail: 'A general question, so no catalog lookup was needed. Written by the language model.',
    });
    return { ran, steps };
  }

  ran.add('search');
  steps.push({
    node: 'search',
    title: 'Searched the parts catalog',
    detail: parts.length ? 'Found matching parts in the product database.' : 'No matching parts found.',
  });

  if (parts.length && CONTEXT_INTENTS.includes(intent)) {
    ran.add('gather_context');
    steps.push({
      node: 'gather_context',
      title: intent === 'diagnose_issue' ? 'Pulled troubleshooting guides' : 'Pulled installation guides',
      detail: 'Semantic search over the knowledge base.',
    });
  }

  if (parts.length) {
    ran.add('recommend');
    steps.push({
      node: 'recommend',
      title: 'Picked the best matches',
      detail: `Showing ${parts.length} part${parts.length === 1 ? '' : 's'}.`,
    });
  }

  ran.add('respond');
  steps.push({
    node: 'respond',
    title: 'Wrote the answer',
    detail: 'Prices, stock and links come straight from the catalog, not from the language model.',
  });

  return { ran, steps };
}

// Next steps the reply's own cards don't already offer (cards carry Install / Check fit).
export function buildFollowUps(message, parts) {
  const top = parts[0];
  const details = (p) => ({ kind: 'send', icon: Info, label: `Tell me more about ${p.partNumber}`, text: `Tell me about ${p.partNumber}` });

  switch (message.intent) {
    case 'search_part':
    case 'diagnose_issue':
    case 'installation_help':
      return top ? [details(top)] : [];
    case 'compatibility_check':
      return message.metadata?.model_number
        ? []
        : [{ kind: 'help', icon: CircleHelp, label: 'Where do I find my model number?' }];
    default:
      return [];
  }
}

// The backend keeps conversation state in Redis and returns it with every
// reply, so the latest reply's metadata is what the agent currently knows.
export function deriveContext(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const m = messages[i];
    if (m.role === 'assistant' && !m.isError && m.metadata) {
      return {
        appliance: m.metadata.appliance_type || null,
        brand: m.metadata.brand || null,
        model: m.metadata.model_number || null,
        awaitingModel:
          m.intent === 'compatibility_check' && !m.metadata.model_number && /model number/i.test(m.content || ''),
      };
    }
  }
  return { appliance: null, brand: null, model: null, awaitingModel: false };
}

// What the customer said was wrong: the messages the agent treated as a diagnosis.
export function reportedProblems(messages) {
  const problems = [];
  messages.forEach((m, i) => {
    const prev = messages[i - 1];
    if (m.role === 'assistant' && m.intent === 'diagnose_issue' && prev?.role === 'user' && !problems.includes(prev.content)) {
      problems.push(prev.content);
    }
  });
  return problems;
}
