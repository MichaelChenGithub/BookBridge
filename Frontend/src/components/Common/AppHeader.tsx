import logo from '../../assets/logo.png';
import './AppHeader.css';

const AppHeader = () => (
  <header className="app-header" role="banner">
    <div className="app-header__inner">
      <div className="app-header__brand">
        <img src={logo} alt="Booker logo" className="app-header__logo" />
        <p className="app-header__title" aria-label="Booker home">
          Booker
        </p>
      </div>
      <div className="app-header__avatar" role="img" aria-label="User avatar">
        <span>BK</span>
      </div>
    </div>
  </header>
);

export default AppHeader;
