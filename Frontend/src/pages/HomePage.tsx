import { useCallback, useEffect, useRef, useState } from 'react';
import AppHeader from '../components/Common/AppHeader';
import BookModal from '../components/Common/BookModal';
import ChatWindow from '../components/Chat/ChatWindow';
import ChatInput from '../components/Chat/ChatInput';
import RecommendationPanel from '../components/Recommendations/RecommendationPanel';
import { useChat } from '../context/ChatContext';
import './HomePage.css';

const HomePage = () => {
  const {
    error,
    handleViewDetails,
    activeRecommendations,
    showRecommendationsForMessage,
    activeRecommendationMessageId,
    addMockRecommendationSet,
  } = useChat();
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const latestRecommendationIdRef = useRef<string | null>(null);
  const showTestingControls = import.meta.env.DEV;

  useEffect(() => {
    if (!activeRecommendationMessageId) {
      latestRecommendationIdRef.current = null;
      return;
    }

    if (latestRecommendationIdRef.current !== activeRecommendationMessageId) {
      latestRecommendationIdRef.current = activeRecommendationMessageId;
      setIsPanelOpen(true);
    }
  }, [activeRecommendationMessageId]);

  const togglePanel = () => setIsPanelOpen((prev) => !prev);
  const handleShowRecommendations = useCallback(
    (messageId: string) => {
      showRecommendationsForMessage(messageId);
      setIsPanelOpen(true);
    },
    [showRecommendationsForMessage]
  );

  const gridClass = `home-page__grid ${isPanelOpen ? '' : 'home-page__grid--panel-hidden'}`.trim();

  return (
    <div className="home-page">
      <div className={gridClass}>
        <section className="home-page__primary">
          <AppHeader />
          {error && (
            <div className="home-page__error" role="alert">
              {error}
            </div>
          )}
          {/* {showTestingControls && (
            <div className="home-page__testing-controls">
              <button
                type="button"
                className="home-page__mock-button"
                onClick={() => {
                  addMockRecommendationSet();
                  setIsPanelOpen(true);
                }}
              >
                Add New Mock Recommendations
              </button>
            </div>
          )} */}
          <div className="home-page__chat-shell">
            <ChatWindow
              onShowRecommendations={handleShowRecommendations}
              isRecommendationPanelOpen={isPanelOpen}
              activeRecommendationMessageId={activeRecommendationMessageId}
            />
            <ChatInput />
          </div>
        </section>

        <RecommendationPanel
          books={activeRecommendations}
          isOpen={isPanelOpen}
          onToggle={togglePanel}
          onViewBook={handleViewDetails}
        />
      </div>
      <BookModal />
    </div>
  );
};

export default HomePage;
