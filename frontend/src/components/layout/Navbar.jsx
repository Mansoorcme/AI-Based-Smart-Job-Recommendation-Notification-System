import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav style={{ padding: '1rem', backgroundColor: '#f0f0f0' }}>
      <Link to="/" style={{ margin: '0 1rem' }}>Home</Link>
      <Link to="/login" style={{ margin: '0 1rem' }}>Login</Link>
      <Link to="/dashboard" style={{ margin: '0 1rem' }}>Dashboard</Link>
      <Link to="/resume" style={{ margin: '0 1rem' }}>Resume</Link>
      <Link to="/matches" style={{ margin: '0 1rem' }}>Matches</Link>
    </nav>
  );
};

export default Navbar;
