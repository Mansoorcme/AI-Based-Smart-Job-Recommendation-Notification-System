import React from 'react';

const JobCard = ({ job }) => {
  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', margin: '1rem 0', borderRadius: '8px' }}>
      <h3 style={{ margin: '0 0 0.5rem 0' }}>{job.title}</h3>
      <p style={{ margin: '0 0 0.5rem 0', fontWeight: 'bold', color: '#333' }}>{job.company}</p>
      <p style={{ margin: '0 0 1rem 0', color: '#666' }}>{job.description}</p>
      {job.location && <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>📍 {job.location}</p>}
      {job.salary_range && <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>💰 {job.salary_range}</p>}
      {job.posting_date && <p style={{ margin: '0 0 1rem 0', fontSize: '0.8rem', color: '#888' }}>Posted: {new Date(job.posting_date).toLocaleDateString()}</p>}
      {job.apply_link && job.apply_link !== '#' && (
        <a
          href={job.apply_link}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            backgroundColor: '#007bff',
            color: 'white',
            padding: '0.5rem 1rem',
            textDecoration: 'none',
            borderRadius: '4px',
            fontWeight: 'bold'
          }}
        >
          Apply Now 🚀
        </a>
      )}
    </div>
  );
};

export default JobCard;
