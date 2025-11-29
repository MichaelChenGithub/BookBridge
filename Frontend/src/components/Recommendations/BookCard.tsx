import { Book } from '../../types';
import defaultCover from '../../assets/default-cover.svg';
import './BookCard.css';

interface BookCardProps {
  book: Book;
  onViewDetails: (book: Book) => void;
}

const BookCard = ({ book, onViewDetails }: BookCardProps) => {
  const author = book.author_name || 'Unknown author';
  const coverSrc = book.primary_image || defaultCover;
  const averageRating = book.average_rating ?? null;
  const ratingCount = book.rating_number ?? null;
  const ratingLabel =
    averageRating !== null
      ? `${averageRating.toFixed(1)} ★${ratingCount ? ` · ${ratingCount.toLocaleString()} ratings` : ''}`
      : null;

  return (
    <article
      className="book-card"
      tabIndex={0}
      role="button"
      onClick={() => onViewDetails(book)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onViewDetails(book);
        }
      }}
    >
      <div className="book-card__media">
        <img
          src={coverSrc}
          alt={`Cover of ${book.title}`}
          loading="lazy"
          onError={(event) => {
            event.currentTarget.src = defaultCover;
          }}
        />
      </div>
      <div className="book-card__content">
        <div className="book-card__meta">
          <p className="book-card__title">{book.title}</p>
          <p className="book-card__author">{author}</p>
        </div>
        {ratingLabel && <p className="book-card__rating">{ratingLabel}</p>}
      </div>
    </article>
  );
};

export default BookCard;
