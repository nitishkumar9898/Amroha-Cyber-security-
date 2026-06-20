import React from 'react';
import './MetaverseView.css';
import MetaverseScene from './MetaverseScene';
import PerformanceHUD from './PerformanceHUD';

const MetaverseView: React.FC = () => {

  return (
    <div className="metaverse-container">
      <div className="metaverse-overlay">
        <h3>Metaverse Threat Simulator</h3>
        <p>Interactive 3D representation of global threat networks.</p>
          <PerformanceHUD />
      </div>
      <MetaverseScene />
    </div>
  );
};

export default MetaverseView;
