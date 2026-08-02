import { Link, NavLink } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">
          <span className="navbar-brand-mark" aria-hidden="true">
            F
          </span>
          <span className="navbar-brand-text">
            <span className="navbar-brand-title">Fortif.ai</span>
            <span className="navbar-brand-sub">Senior Assistant</span>
          </span>
        </Link>
      </div>

      <div className="navbar-menu">
        <NavLink to="/" end className="navbar-link">
          Home
        </NavLink>
        <NavLink to="/memories" className="navbar-link">
          Memories
        </NavLink>
        <NavLink to="/hazard-detector" className="navbar-link">
          Hazard Detector
        </NavLink>
        <NavLink to="/voice" className="navbar-link">
          Voice Commands
        </NavLink>
      </div>
    </nav>
  )
}

export default Navbar
