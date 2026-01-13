import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Fortif.ai Memory Dashboard</Link>
      </div>

      <div className="navbar-menu">
        <Link to="/" className="navbar-link">
          Dashboard
        </Link>
        <Link to="/memories" className="navbar-link">
          Memories
        </Link>
      </div>
    </nav>
  )
}

export default Navbar
