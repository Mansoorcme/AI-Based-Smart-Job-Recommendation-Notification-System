import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';

const Dashboard = () => {
  const [resumeStatus, setResumeStatus] = useState('Not uploaded');
  const [totalMatches, setTotalMatches] = useState(0);
  const [loading, setLoading] = useState(true);
  const { token } = useContext(AuthContext);

  useEffect(() => {
    if (token) {
      fetchDashboardData();
    }
  }, [token]);

  const fetchDashboardData = async () => {
    try {
      // Assuming endpoints for resume status and matches
      const resumeResponse = await api.get('/resume/status');
      setResumeStatus(resumeResponse.data.status || 'Uploaded');
      const matchesResponse = await api.get('/match/count');
      setTotalMatches(matchesResponse.data.count || 0);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Dashboard</h1>
      <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
        <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', flex: 1 }}>
          <h3>Resume Status</h3>
          <p>{resumeStatus}</p>
        </div>
        <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', flex: 1 }}>
          <h3>Total Job Matches</h3>
          <p>{totalMatches}</p>
        </div>
      </div>
      <div>
        <Link to="/resume" style={{ margin: '0 1rem', padding: '0.5rem 1rem', backgroundColor: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
          Upload Resume
        </Link>
        <Link to="/matches" style={{ margin: '0 1rem', padding: '0.5rem 1rem', backgroundColor: '#28a745', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
          View Matches
        </Link>
      </div>
    </div>
  );
};

export default Dashboard;
