import { Message } from '../../types';
import Logo from '../../assets/logo.png';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: Message;
  onShowRecommendations?: (messageId: string) => void;
  isRecommendationPanelOpen?: boolean;
  isActiveRecommendation?: boolean;
}

const AiAvatar = () => (
  <img src={Logo} alt="BookBridge logo" className="message-bubble__ai-logo" loading="lazy" />
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
      {/* {showAvatar && (
        <div className="message-bubble__avatar" aria-hidden="true">
          <AiAvatar />
        </div>
      )} */}
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
