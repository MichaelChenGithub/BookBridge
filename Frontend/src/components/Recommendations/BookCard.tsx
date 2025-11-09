import { Book } from '../../types';
import defaultCover from '../../assets/default-cover.svg';
import './BookCard.css';

interface BookCardProps {
  book: Book;
  onViewDetails: (book: Book) => void;
}

const BookCard = ({ book, onViewDetails }: BookCardProps) => (
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
        src={book.coverUrl || defaultCover}
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
        <p className="book-card__author">{book.author}</p>
      </div>
      <p className="book-card__summary">{book.summary}</p>
      <div className="book-card__footer">
        <span className="book-card__chip">{book.source || 'AI Pick'}</span>
      </div>
    </div>
  </article>
);

export default BookCard;
