import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { MotionConfig } from 'framer-motion';
import './styles/tokens.css';
import './styles/layout.css';
import './styles/chat.css';
import { Composer } from './components/Composer';
import { MessageList } from './components/MessageList';
import { Drawer, VideoModal } from './components/Overlay';
import { RepairPanel } from './components/RepairPanel';
import { TopBar } from './components/TopBar';
import { Welcome } from './components/Welcome';
import { ChatActions } from './context/ChatActions';
import { useChat } from './hooks/useChat';
import { useShortlist } from './hooks/useShortlist';
import { useTheme } from './hooks/useTheme';
import { deriveContext, reportedProblems } from './lib/replies';

function App() {
  const { isDark, toggle: toggleTheme } = useTheme();
  const { messages, loading, send, retry, reset } = useChat();
  const shortlist = useShortlist();

  const [draft, setDraft] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [video, setVideo] = useState(null);
  const inputRef = useRef(null);
  const scrollRef = useRef(null);

  const context = useMemo(() => deriveContext(messages), [messages]);
  const problems = useMemo(() => reportedProblems(messages), [messages]);

  // Keep the newest message in view.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  const prefill = useCallback((text) => {
    setDraft(text);
    setDrawerOpen(false);
    requestAnimationFrame(() => {
      const el = inputRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(text.length, text.length);
    });
  }, []);

  const sendDraft = useCallback(() => {
    if (send(draft)) setDraft('');
  }, [draft, send]);

  const newRepair = useCallback(() => {
    reset();
    shortlist.clear();
    setDraft('');
  }, [reset, shortlist]);

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const closeVideo = useCallback(() => setVideo(null), []);
  const addModel = useCallback(() => prefill('My model number is '), [prefill]);

  const actions = useMemo(
    () => ({ send, retry, prefill, openVideo: setVideo, shortlist, context, loading }),
    [send, retry, prefill, shortlist, context, loading]
  );

  const panel = (onClose) => (
    <RepairPanel context={context} problems={problems} shortlist={shortlist} onAddModel={addModel} onClose={onClose} />
  );

  return (
    <MotionConfig reducedMotion="user">
      <ChatActions.Provider value={actions}>
        <div className="app">
          <TopBar
            isDark={isDark}
            onToggleTheme={toggleTheme}
            onOpenRepair={() => setDrawerOpen(true)}
            shortlistCount={shortlist.items.length}
            onNewRepair={newRepair}
            canReset={messages.length > 0 || shortlist.items.length > 0}
          />

          <div className="workspace">
            <main className="chat">
              <div className="chat__scroll" ref={scrollRef}>
                <div className="chat__inner">
                  {messages.length === 0 ? (
                    <Welcome onAsk={send} />
                  ) : (
                    <MessageList messages={messages} loading={loading} />
                  )}
                </div>
              </div>
              <div className="chat__composer">
                <Composer
                  ref={inputRef}
                  value={draft}
                  onChange={setDraft}
                  onSend={sendDraft}
                  loading={loading}
                  placeholder={context.awaitingModel ? 'Your model number, e.g. WDT780SAEM1' : 'Ask about a part or a problem…'}
                />
              </div>
            </main>

            <aside className="panel" aria-label="Your repair">
              {panel()}
            </aside>
          </div>

          <Drawer open={drawerOpen} onClose={closeDrawer} label="Your repair">
            {panel(closeDrawer)}
          </Drawer>
          <VideoModal video={video} onClose={closeVideo} />
        </div>
      </ChatActions.Provider>
    </MotionConfig>
  );
}

export default App;
