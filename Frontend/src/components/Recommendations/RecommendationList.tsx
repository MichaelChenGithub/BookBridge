import { Book } from '../../types';
import BookCard from './BookCard';
import './RecommendationList.css';

interface RecommendationListProps {
  books: Book[];
  onViewBook: (book: Book) => void;
  orientation?: 'horizontal' | 'vertical';
}

const RecommendationList = ({ books, onViewBook, orientation = 'vertical' }: RecommendationListProps) => (
  <div className={`recommendation-list recommendation-list--${orientation}`} role="list">
    {books.map((book) => (
      <div key={book.id} role="listitem" className="recommendation-list__item">
        <BookCard book={book} onViewDetails={onViewBook} />
      </div>
    ))}
  </div>
);

export default RecommendationList;
