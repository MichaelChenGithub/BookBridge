import { Message } from '../../types';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: Message;
  onShowRecommendations?: (messageId: string) => void;
  isRecommendationPanelOpen?: boolean;
  isActiveRecommendation?: boolean;
}

const AiAvatar = () => (
  <svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">
    <path
      d="M6 9a3 3 0 0 1 3-3h14a3 3 0 0 1 3 3v13.4c0 .78-.87 1.23-1.52.77l-4.96-3.47a1.5 1.5 0 0 0-1.7 0L12.9 23.2a1 1 0 0 1-1.52-.82z"
      fill="currentColor"
    />
  </svg>
);

const MessageBubble = ({
  message,
  onShowRecommendations,
  isRecommendationPanelOpen,
  isActiveRecommendation,
}: MessageBubbleProps) => {
  const modifier = `message-bubble--${message.sender}`;
  const showAvatar = message.sender === 'ai';
  const hasRecommendations = !!message.recommendations?.length && message.sender === 'ai';
  const isActive = Boolean(isActiveRecommendation);
  const buttonLabel =
    isRecommendationPanelOpen && isActive ? 'Recommended books open' : 'Show recommended books';

  return (
    <div className={`message-bubble ${modifier}`}>
      {showAvatar && (
        <div className="message-bubble__avatar" aria-hidden="true">
          <AiAvatar />
        </div>
      )}
      <div className="message-bubble__body">
        <p className="message-bubble__text">{message.text}</p>

        {hasRecommendations && (
          <div className="message-bubble__actions">
            <p className="message-bubble__hint">
              {message.recommendations!.length} curated pick
              {message.recommendations!.length > 1 ? 's' : ''} attached.
            </p>
            <button
              type="button"
              className="message-bubble__button"
              onClick={() => {
                onShowRecommendations?.(message.id);
              }}
              disabled={isRecommendationPanelOpen && isActive}
            >
              {buttonLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
