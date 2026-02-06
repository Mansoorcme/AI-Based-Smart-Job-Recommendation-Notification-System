import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ResumeInsights from './pages/ResumeInsights';
import JobMatches from './pages/JobMatches';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/resume" element={<ResumeInsights />} />
            <Route path="/matches" element={<JobMatches />} />
          </Routes>
        </Layout>
      </Router>
    </AuthProvider>
  );
}

export default App;
