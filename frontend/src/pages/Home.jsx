import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div style={{ textAlign: 'center', padding: '2rem' }}>
      <h1>Welcome to AI-Based Smart Job Recommendation & ATS Matching System</h1>
      <p>Find your perfect job match with our advanced AI technology.</p>
      <div style={{ marginTop: '2rem' }}>
        <Link to="/login" style={{ margin: '0 1rem', padding: '0.5rem 1rem', backgroundColor: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
          Login
        </Link>
        <Link to="/dashboard" style={{ margin: '0 1rem', padding: '0.5rem 1rem', backgroundColor: '#28a745', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
          Dashboard
        </Link>
      </div>
    </div>
  );
};

export default Home;
