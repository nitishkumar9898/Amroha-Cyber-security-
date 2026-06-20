import React, { useState } from 'react';
import { startTraining, getResults } from '../api/training';

const TrainingControls: React.FC = () => {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>('Idle');

  const handleStart = async () => {
    try {
      const userId = 'officer_sharma'; // In a real app, pull from auth context
      const payload = { user_id: userId, scenario_name: 'AR/VR Threat Sim' };
      const resp = await startTraining(payload);
      setSessionId(resp.id);
      setStatus('Running');
    } catch (e) {
      console.error(e);
      setStatus('Error starting session');
    }
  };

  const fetchResults = async () => {
    if (!sessionId) return;
    try {
      const results = await getResults(sessionId);
      console.log('Training results:', results);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="training-controls" style={{ position: 'absolute', top: '1rem', left: '1rem' }}>
      <button onClick={handleStart} disabled={status === 'Running'}>Start Training</button>
      {sessionId && (
        <>
          <p>Session ID: {sessionId}</p>
          <button onClick={fetchResults}>Fetch Results</button>
        </>
      )}
      <p>Status: {status}</p>
    </div>
  );
};

export default TrainingControls;
