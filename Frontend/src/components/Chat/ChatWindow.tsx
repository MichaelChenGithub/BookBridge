import MessageBubble from './MessageBubble';
import LoadingSpinner from '../Common/LoadingSpinner';
import { useChat } from '../../context/ChatContext';
import { useChatScroll } from '../../hooks/useChatScroll';
import './ChatWindow.css';

interface ChatWindowProps {
  onShowRecommendations?: (messageId: string) => void;
  isRecommendationPanelOpen?: boolean;
  activeRecommendationMessageId?: string | null;
}

const ChatWindow = ({
  onShowRecommendations,
  isRecommendationPanelOpen,
  activeRecommendationMessageId,
}: ChatWindowProps) => {
  const { messages, isLoading } = useChat();
  const listRef = useChatScroll<HTMLDivElement>(messages);

  return (
    <section className="chat-window" aria-live="polite">
      <div className="chat-window__messages" ref={listRef} role="log">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onShowRecommendations={onShowRecommendations}
            isRecommendationPanelOpen={isRecommendationPanelOpen}
            isActiveRecommendation={message.id === activeRecommendationMessageId}
          />
        ))}
        {isLoading && <LoadingSpinner />}
      </div>
    </section>
  );
};

export default ChatWindow;
