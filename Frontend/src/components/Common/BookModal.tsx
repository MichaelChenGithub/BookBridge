import { useEffect } from 'react';
import { useChat } from '../../context/ChatContext';
import defaultCover from '../../assets/default-cover.svg';
import './BookModal.css';

const BookModal = () => {
  const { selectedBook, handleCloseModal } = useChat();

  useEffect(() => {
    if (!selectedBook) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') handleCloseModal();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedBook, handleCloseModal]);

  if (!selectedBook) return null;

  const { title, author_name, primary_image, average_rating, rating_number } = selectedBook;
  const author = author_name || 'Unknown author';
  const coverSrc = primary_image || defaultCover;
  const averageRating = average_rating ?? null;
  const ratingCount = rating_number ?? null;
  const hasStats = averageRating !== null || ratingCount !== null;

  return (
    <div className="book-modal" role="dialog" aria-modal="true" onClick={handleCloseModal}>
      <div className="book-modal__content" onClick={(e) => e.stopPropagation()}>
        <button className="book-modal__close" onClick={handleCloseModal} aria-label="Close details">
          Close
        </button>
        <div className="book-modal__body">
          <img
            src={coverSrc}
            alt={`Cover of ${title}`}
            className="book-modal__cover"
            onError={(event) => {
              event.currentTarget.src = defaultCover;
            }}
          />
          <div>
            <p className="book-modal__label">Recommended Book</p>
            <h2 className="book-modal__title">{title}</h2>
            <p className="book-modal__author">{author}</p>
            {hasStats && (
              <div className="book-modal__stats">
                {averageRating !== null && (
                  <p className="book-modal__stat">Average rating: {averageRating.toFixed(1)} ★</p>
                )}
                {ratingCount !== null && (
                  <p className="book-modal__stat">Ratings count: {ratingCount.toLocaleString()}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookModal;
