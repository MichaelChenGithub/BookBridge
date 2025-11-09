import spinner from '../../assets/spinner.svg';
import './LoadingSpinner.css';

const LoadingSpinner = () => (
  <div className="loading-spinner" role="status" aria-live="polite">
    <img src={spinner} alt="Loading" className="loading-spinner__icon" />
    <span className="loading-spinner__text">Thinking...</span>
  </div>
);

export default LoadingSpinner;
