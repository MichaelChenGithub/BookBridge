import { FormEvent, useState } from 'react';
import sendIcon from '../../assets/send-icon.svg';
import { useChat } from '../../context/ChatContext';
import './ChatInput.css';

const ChatInput = () => {
  const { handleSendMessage, isLoading } = useChat();
  const [inputText, setInputText] = useState('');

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!inputText.trim()) return;
    await handleSendMessage(inputText);
    setInputText('');
  };

  return (
    <form className="chat-input" onSubmit={onSubmit} aria-label="Send a book prompt">
      <label htmlFor="chat-input-field" className="chat-input__label visually-hidden">
        Describe books you love
      </label>
      <div className="chat-input__controls">
        <input
          id="chat-input-field"
          className="chat-input__field"
          type="text"
          placeholder="Describe books you love..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={isLoading}
          autoComplete="off"
        />
        <button type="submit" className="chat-input__button" disabled={isLoading} aria-label="Send message">
          <img src={sendIcon} alt="" className="chat-input__icon" />
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
