import React, { useState, useCallback } from 'react';
import { Book, Message } from '../types';
import { fetchChatResponse } from '../services/api';

interface RecommendationHistoryEntry {
  messageId: string;
  books: Book[];
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  selectedBook: Book | null;
  error: string | null;
  recommendationHistory: RecommendationHistoryEntry[];
  activeRecommendationMessageId: string | null;
  activeRecommendations: Book[];
}

interface ChatActions {
  handleSendMessage: (text: string) => Promise<void>;
  handleViewDetails: (book: Book) => void;
  handleCloseModal: () => void;
  showRecommendationsForMessage: (messageId: string) => void;
}

export const ChatContext =
  React.createContext<ChatState & ChatActions | undefined>(undefined);

export const useChat = () => {
  const ctx = React.useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
};

interface ChatProviderProps {
  children: React.ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recommendationHistory, setRecommendationHistory] = useState<RecommendationHistoryEntry[]>([]);
  const [activeRecommendationMessageId, setActiveRecommendationMessageId] = useState<string | null>(null);

  const persistRecommendations = useCallback((messageId: string, books: Book[]) => {
    if (!books.length) return;
    setRecommendationHistory((prev) => [...prev, { messageId, books }]);
    setActiveRecommendationMessageId(messageId);
  }, []);

  const handleSendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userHistory = messages.filter((message) => message.sender === 'user').map((message) => message.text);
    const userMsg: Message = { id: crypto.randomUUID(), sender: 'user', text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      const aiMsg = await fetchChatResponse(trimmed, userHistory);
      setMessages((prev) => [...prev, aiMsg]);

      const aiRecommendations = aiMsg.recommendations ?? [];
      if (aiRecommendations.length) {
        persistRecommendations(aiMsg.id, aiRecommendations);
      }
    } catch (err) {
      setError((err as Error).message || 'Unable to fetch response.');
    } finally {
      setIsLoading(false);
    }
  }, [messages, persistRecommendations]);

  const handleViewDetails = (book: Book) => setSelectedBook(book);
  const handleCloseModal = () => setSelectedBook(null);

  const activeRecommendations = React.useMemo(() => {
    if (!activeRecommendationMessageId) return [];
    return recommendationHistory.find((entry) => entry.messageId === activeRecommendationMessageId)?.books || [];
  }, [activeRecommendationMessageId, recommendationHistory]);

  const showRecommendationsForMessage = useCallback(
    (messageId: string) => {
      const hasEntry = recommendationHistory.some((entry) => entry.messageId === messageId);
      if (hasEntry) setActiveRecommendationMessageId(messageId);
    },
    [recommendationHistory]
  );

  const value = React.useMemo(
    () => ({
      messages,
      isLoading,
      selectedBook,
      error,
      handleSendMessage,
      handleViewDetails,
      handleCloseModal,
      recommendationHistory,
      activeRecommendationMessageId,
      activeRecommendations,
      showRecommendationsForMessage,
    }),
    [
      messages,
      isLoading,
      selectedBook,
      error,
      handleSendMessage,
      recommendationHistory,
      activeRecommendationMessageId,
      activeRecommendations,
      showRecommendationsForMessage,
    ]
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
