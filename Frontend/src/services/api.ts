import axios from 'axios';
import { Book, Message } from '../types';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:9090',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

API.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Network Error';
    return Promise.reject(new Error(msg));
  }
);

interface RecommendationRequestBody {
  prompt: string;
  history?: string[];
}

type RecommendationResponseBody = Book[];

const toAiMessage = (books: Book[]): Message => {
  const text = books.length
    ? 'Here are your book recommendations.'
    : "Share a little more about what you're into.";

  return {
    id: crypto.randomUUID(),
    sender: 'ai',
    text,
    recommendations: books,
  };
};

export const fetchChatResponse = async (prompt: string, history: string[]): Promise<Message> => {
  const payload: RecommendationRequestBody = {
    prompt,
    history: history.length ? history : [],
  };

  const { data } = await API.post<RecommendationResponseBody>(
    '/recommendations',
    payload
  );

  return toAiMessage(data);
};
