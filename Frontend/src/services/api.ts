import axios from 'axios';
import { Book, Message } from '../types';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
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

interface ChatRequestBody {
  history: Message[];
}

type ChatResponseBody = Message;

const mockBooks: Book[] = [
  {
    id: 'midnight-library',
    title: 'The Midnight Library',
    author: 'Matt Haig',
    summary:
      'A moving story about Nora Seed, who navigates alternate lives in a magical library to discover what truly makes life worth living.',
    coverUrl:
      'https://images.unsplash.com/photo-1474366521946-c3d4b507abf2?auto=format&fit=crop&w=320&q=80',
    source: 'Popular Pick',
  },
  {
    id: 'atomic-habits',
    title: 'Atomic Habits',
    author: 'James Clear',
    summary:
      'A practical handbook for building better habits through tiny changes that compound into remarkable results over time.',
    coverUrl:
      'https://images.unsplash.com/photo-1455885666463-1c1ecaf2ed26?auto=format&fit=crop&w=320&q=80',
    source: 'Self-Help',
  },
  {
    id: 'project-hail-mary',
    title: 'Project Hail Mary',
    author: 'Andy Weir',
    summary:
      'A lone astronaut must save Earth by solving a cosmic mystery aboard a faraway spacecraft in this high-stakes science adventure.',
    coverUrl:
      'https://images.unsplash.com/photo-1463320726281-696a485928c7?auto=format&fit=crop&w=320&q=80',
    source: 'Sci-Fi Gem',
  },
];

export const newMockRecommendations: Book[] = [
  {
    id: 'luminaries-collective',
    title: 'The Luminaries Collective',
    author: 'Harper Lane',
    summary: 'A band of archivists uncover messages hidden inside constellations and race to decode a mythic prophecy.',
    coverUrl: 'https://images.unsplash.com/photo-1455885666463-1c1ecaf2ed26?auto=format&fit=crop&w=320&q=80',
    source: 'Speculative Fiction',
  },
  {
    id: 'inkbound-letters',
    title: 'Inkbound Letters',
    author: 'Nia Calderón',
    summary: 'Two historians fall in love while restoring a forgotten seaside library filled with marginalia from past readers.',
    coverUrl: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=320&q=80',
    source: 'Literary Romance',
  },
  {
    id: 'atlas-of-rivers',
    title: 'Atlas of Rivers',
    author: 'Callum Reyes',
    summary: 'An immersive travelogue that follows legendary waterways and the communities who depend on them.',
    coverUrl: 'https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=320&q=80',
    source: 'Narrative Nonfiction',
  },
  {
    id: 'midnight-botanist',
    title: 'The Midnight Botanist',
    author: 'Sora Bennett',
    summary: 'A young scientist cultivates night-blooming plants that reveal memories, forcing her to confront her family’s past.',
    coverUrl: 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&w=320&q=80',
    source: 'Magical Realism',
  },
];

const mockMessageText =
  "Based on your interests, I've curated these popular books for you. They're highly rated and loved by readers across different genres!";

const getRandomRecommendations = (count: number): Book[] => {
  const source = newMockRecommendations.length ? newMockRecommendations : mockBooks;
  const pool = source.map((book) => ({ ...book }));
  if (pool.length <= count) return pool;

  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }

  return pool.slice(0, count);
};

const shouldUseMocks = (import.meta.env.VITE_USE_MOCKS ?? 'true') !== 'false';

const buildMockResponse = (): Message => ({
  id: crypto.randomUUID(),
  sender: 'ai',
  text: mockMessageText,
  recommendations: getRandomRecommendations(3),
});

export const fetchChatResponse = async (
  currentHistory: Message[]
): Promise<Message> => {
  if (shouldUseMocks) {
    return new Promise((resolve) => {
      setTimeout(() => resolve(buildMockResponse()), 600);
    });
  }

  const { data } = await API.post<ChatResponseBody>('/api/chat', {
    history: currentHistory,
  } satisfies ChatRequestBody);
  return data;
};
