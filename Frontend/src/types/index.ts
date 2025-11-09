/** Represents a book entity */
export interface Book {
  id: string;
  title: string;
  author: string;
  summary: string;
  coverUrl?: string;
  source?: string;
}

/** Represents a chat message */
export interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  recommendations?: Book[];
}
