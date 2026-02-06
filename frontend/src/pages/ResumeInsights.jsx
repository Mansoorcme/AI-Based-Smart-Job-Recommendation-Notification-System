import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';

const ResumeInsights = () => {
  const { resumeId } = useParams();
  const [recommendations, setRecommendations] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (resumeId) {
      fetchRoleRecommendations();
    }
  }, [resumeId]);

  const fetchRoleRecommendations = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/role/recommendations/${resumeId}`);
      setRecommendations(response.data.recommendations);
    } catch (err) {
      setError('Failed to fetch role recommendations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleSelect = async (role) => {
    try {
      await api.post(`/role/select/${resumeId}`, { selected_role: role });
      setSelectedRole(role);
      // TODO: Navigate to job discovery or trigger job search
    } catch (err) {
      setError('Failed to select role');
      console.error(err);
    }
  };

  if (loading) {
    return <div className="container mx-auto px-4 py-8">Loading role recommendations...</div>;
  }

  if (error) {
    return <div className="container mx-auto px-4 py-8 text-red-600">{error}</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Resume Insights & Role Recommendations</h1>

      {recommendations && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Career Positioning</h2>
          <p className="text-gray-700 mb-4">{recommendations.diagnostic}</p>

          <h3 className="text-lg font-semibold mb-4">Recommended Roles</h3>
          <div className="space-y-4">
            {recommendations.roles.map((role, index) => (
              <div key={index} className="border rounded-lg p-4">
                <h4 className="font-semibold text-lg mb-2">{role.title}</h4>
                <p className="text-gray-700 mb-3">{role.explanation}</p>

                <h5 className="font-medium mb-2">Key Tasks:</h5>
                <ul className="list-disc list-inside text-gray-600 mb-4">
                  {role.tasks.map((task, taskIndex) => (
                    <li key={taskIndex}>{task}</li>
                  ))}
                </ul>

                {!selectedRole && (
                  <button
                    onClick={() => handleRoleSelect(role.title)}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                  >
                    Select This Role
                  </button>
                )}
              </div>
            ))}
          </div>

          {recommendations.decision_guide && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Decision Guide</h3>
              <pre className="text-gray-700 whitespace-pre-wrap">{recommendations.decision_guide}</pre>
            </div>
          )}
        </div>
      )}

      {selectedRole && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          <strong>Role Selected:</strong> {selectedRole}
          <p className="mt-2">Ready for job discovery and ATS scoring!</p>
        </div>
      )}
    </div>
  );
};

export default ResumeInsights;
