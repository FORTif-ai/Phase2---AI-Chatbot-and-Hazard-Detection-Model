import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">
          <span className="navbar-brand-title">Fortif.ai</span>
          <span className="navbar-brand-sub">Senior Assistant</span>
        </Link>
      </div>

      <div className="navbar-menu">
        <Link to="/" className="navbar-link">
          Home
        </Link>
        <Link to="/memories" className="navbar-link">
          Memories
        </Link>
        <Link to="/hazard-detector" className="navbar-link">
          Hazard Detector
        </Link>
        <Link to="/voice" className="navbar-link">
          Voice Commands
        </Link>
      </div>
    </nav>
  )
}

export default Navbar
