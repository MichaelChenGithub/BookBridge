import { ChatProvider } from './context/ChatContext';
import HomePage from './pages/HomePage';

const App = () => (
  <ChatProvider>
    <HomePage />
  </ChatProvider>
);

export default App;
