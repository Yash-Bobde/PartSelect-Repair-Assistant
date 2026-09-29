import { createContext, useContext } from 'react';

// Actions that cards and chips deep in the message list need: send a message,
// pre-fill the composer, open a video, manage the shortlist, read the context.
export const ChatActions = createContext(null);

export const useChatActions = () => useContext(ChatActions);
