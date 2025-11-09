import { Book } from '../../types';
import RecommendationList from './RecommendationList';
import './RecommendationPanel.css';

interface RecommendationPanelProps {
  books: Book[];
  isOpen: boolean;
  onToggle: () => void;
  onViewBook: (book: Book) => void;
}

const RecommendationPanel = ({ books, isOpen, onToggle, onViewBook }: RecommendationPanelProps) => {
  const countLabel = books.length ? `${books.length} book${books.length > 1 ? 's' : ''} found` : 'No books yet';
  const toggleLabel = isOpen ? 'Hide recommended books' : 'Show recommended books';

  return (
    <aside
      className={`recommendation-panel ${isOpen ? '' : 'recommendation-panel--collapsed'}`}
      aria-hidden={!isOpen}
      role="complementary"
    >
      <div className="recommendation-panel__header">
        <div>
          <p className="recommendation-panel__title">Recommended Books</p>
          <p className="recommendation-panel__subtitle">{countLabel}</p>
        </div>
        <button type="button" className="recommendation-panel__toggle" onClick={onToggle} aria-label={toggleLabel}>
          {isOpen ? 'Hide' : 'Show'}
        </button>
      </div>
      {isOpen && (
        books.length ? (
          <RecommendationList books={books} onViewBook={onViewBook} orientation="vertical" />
        ) : (
          <div className="recommendation-panel__empty">
            <p>Ask for recommendations to see curated picks here.</p>
          </div>
        )
      )}
    </aside>
  );
};

export default RecommendationPanel;
