/** Represents a book entity */
export interface Book {
  /** Backend ASIN identifier for the book */
  asin: string;
  title: string;
  author_name?: string | null;
  average_rating?: number | null;
  rating_number?: number | null;
  primary_image?: string | null;
}

/** Represents a chat message */
export interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  recommendations?: Book[];
}
