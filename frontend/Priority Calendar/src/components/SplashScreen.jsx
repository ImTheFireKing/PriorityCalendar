import './SplashScreen.css';
import logo from '../assets/PriorityCalendarFullLogoTransparent.png'; // ← your full icon here

export default function SplashScreen() {
  return (
    <div className="splash">
      <div className="splash-inner">
        <img src={logo} alt="Priority Calendar" className="splash-logo" />
        <div className="splash-spinner" />
        <p className="splash-text">Loading your calendar...</p>
      </div>
    </div>
  );
}