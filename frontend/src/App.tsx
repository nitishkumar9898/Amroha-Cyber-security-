import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { InvestigationRange } from './components/InvestigationRange';
import { Analytics } from './components/Analytics';
import { Reports } from './components/Reports';
import { ActivityLog } from './components/ActivityLog';
import { AdminPanel } from './components/AdminPanel';
import { About } from './components/About';
import { ResearchHub } from './components/ResearchHub';
import MetaverseView from './components/MetaverseView';
import { AIChatBot } from './components/AIChatBot';
import BehavioralDashboard from './components/BehavioralDashboard';
import { SupplyChainDashboard } from './components/SupplyChainDashboard';
import { OSINTDashboard } from './components/OSINTDashboard';
import ResponseForgeDashboard from './components/ResponseForgeDashboard';
import HardwareForensixDashboard from './components/HardwareForensixDashboard';
import EvolvoAIDashboard from './components/EvolvoAIDashboard';
import CollabGuardDashboard from './components/CollabGuardDashboard';
import RansomGuardDashboard from './components/RansomGuardDashboard';
import CloudForensixDashboard from './components/CloudForensixDashboard';
import BioThreatForgeDashboard from './components/BioThreatForgeDashboard';
import { CommForensixDashboard } from './components/CommForensixDashboard';
import NetGuardDashboard from './components/NetGuardDashboard';
import EthicsForgeDashboard from './components/EthicsForgeDashboard';
import ResilientForgeDashboard from './components/ResilientForgeDashboard';
import SwarmForgeDashboard from './components/SwarmForgeDashboard';
import NeuroGuardDashboard from './components/NeuroGuardDashboard';
import SpaceGuardDashboard from './components/SpaceGuardDashboard';
import ClimateShieldDashboard from './components/ClimateShieldDashboard';
import NanoQuantumDashboard from './components/NanoQuantumDashboard';
import InnovateGuardDashboard from './components/InnovateGuardDashboard';
import MetaForgeDashboard from './components/MetaForgeDashboard';
import DroneGuardDashboard from './components/DroneGuardDashboard';
import MetaGuardDashboard from './components/MetaGuardDashboard';
import FinGuardDashboard from './components/FinGuardDashboard';
import HumanForgeDashboard from './components/HumanForgeDashboard';
import GridShieldDashboard from './components/GridShieldDashboard';
import PromptDefenderDashboard from './components/PromptDefenderDashboard';
import GlobalJurixDashboard from './components/GlobalJurixDashboard';
import ZeroTrustForgeDashboard from './components/ZeroTrustForgeDashboard';
import OmniSimulatorDashboard from './components/OmniSimulatorDashboard';
import AudioForensixDashboard from './components/AudioForensixDashboard';
import VisualForensixDashboard from './components/VisualForensixDashboard';
import APTHunterDashboard from './components/APTHunterDashboard';
import RiskNovaDashboard from './components/RiskNovaDashboard';
import CampaignGuardDashboard from './components/CampaignGuardDashboard';

// Batch 1-4 Imports
import { ModelDefenderDashboard } from './components/ModelDefenderDashboard';
import { FirmwareGuardDashboard } from './components/FirmwareGuardDashboard';
import { PsyOpsForgeDashboard } from './components/PsyOpsForgeDashboard';
import { CorrelixDashboard } from './components/CorrelixDashboard';
import { CollabSpaceDashboard } from './components/CollabSpaceDashboard';
import { LearnForgeDashboard } from './components/LearnForgeDashboard';
import { BehavixDashboard } from './components/BehavixDashboard';
import { UndergroundForgeDashboard } from './components/UndergroundForgeDashboard';
import { ZeroDayForgeDashboard } from './components/ZeroDayForgeDashboard';
import { LinguaGuardDashboard } from './components/LinguaGuardDashboard';
import { AnomalyMasterDashboard } from './components/AnomalyMasterDashboard';
import { VoiceGuardDashboard } from './components/VoiceGuardDashboard';
import { SmartCityGuardDashboard } from './components/SmartCityGuardDashboard';
import { DeFiGuardDashboard } from './components/DeFiGuardDashboard';
import { AdversaryDefenderDashboard } from './components/AdversaryDefenderDashboard';
import { SovereignGuardDashboard } from './components/SovereignGuardDashboard';
import { LegacyShieldDashboard } from './components/LegacyShieldDashboard';

import { Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  return (
    <>
      <Header />
      <main className="app">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/investigation" element={<InvestigationRange />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/activity" element={<ActivityLog />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/about" element={<About />} />
          <Route path="/research" element={<ResearchHub />} />
          <Route path="/metaverse" element={<MetaverseView />} />
          <Route path="/behavioral" element={<BehavioralDashboard />} />
          <Route path="/supplyguard" element={<SupplyChainDashboard />} />
          <Route path="/osint" element={<OSINTDashboard />} />
          <Route path="/responseforge" element={<ResponseForgeDashboard />} />
          <Route path="/hardwareforensix" element={<HardwareForensixDashboard />} />
          <Route path="/evolvoai" element={<EvolvoAIDashboard />} />
          <Route path="/collabguard" element={<CollabGuardDashboard />} />
          <Route path="/ransomguard" element={<RansomGuardDashboard />} />
          <Route path="/cloudforensix" element={<CloudForensixDashboard />} />
          <Route path="/commforensix" element={<CommForensixDashboard />} />
          <Route path="/netguard" element={<NetGuardDashboard />} />
          <Route path="/ethicsforge" element={<EthicsForgeDashboard />} />
          <Route path="/resilientforge" element={<ResilientForgeDashboard />} />
          <Route path="/swarmforge" element={<SwarmForgeDashboard />} />
          <Route path="/neuroguard" element={<NeuroGuardDashboard />} />
          <Route path="/spaceguard" element={<SpaceGuardDashboard />} />
          <Route path="/climateshield" element={<ClimateShieldDashboard />} />
          <Route path="/nanoquantum" element={<NanoQuantumDashboard />} />
          <Route path="/innovateguard" element={<InnovateGuardDashboard />} />
          <Route path="/metaforge" element={<MetaForgeDashboard />} />
          <Route path="/droneguard" element={<DroneGuardDashboard />} />
          <Route path="/metaguard" element={<MetaGuardDashboard />} />
          <Route path="/finguard" element={<FinGuardDashboard />} />
          <Route path="/humanforge" element={<HumanForgeDashboard />} />
          <Route path="/gridshield" element={<GridShieldDashboard />} />
          <Route path="/promptdefender" element={<PromptDefenderDashboard />} />
          <Route path="/globaljurix" element={<GlobalJurixDashboard />} />
          <Route path="/zerotrustforge" element={<ZeroTrustForgeDashboard />} />
          <Route path="/omnisimulator" element={<OmniSimulatorDashboard />} />
          <Route path="/audioforensix" element={<AudioForensixDashboard />} />
          <Route path="/visualforensix" element={<VisualForensixDashboard />} />
        <Route path="/biothreatforge" element={<BioThreatForgeDashboard />} />
        <Route path="/apthunter" element={<APTHunterDashboard />} />
        <Route path="/risknova" element={<RiskNovaDashboard />} />
        <Route path="/campaignguard" element={<CampaignGuardDashboard />} />
        
        {/* Batch 1-4 Routes */}
        <Route path="/modeldefender" element={<ModelDefenderDashboard />} />
        <Route path="/firmwareguard" element={<FirmwareGuardDashboard />} />
        <Route path="/psyopsforge" element={<PsyOpsForgeDashboard />} />
        <Route path="/correlix" element={<CorrelixDashboard />} />
        <Route path="/collabspace" element={<CollabSpaceDashboard />} />
        <Route path="/learnforge" element={<LearnForgeDashboard />} />
        <Route path="/behavix-new" element={<BehavixDashboard />} />
        <Route path="/undergroundforge" element={<UndergroundForgeDashboard />} />
        <Route path="/zerodayforge" element={<ZeroDayForgeDashboard />} />
        <Route path="/linguaguard" element={<LinguaGuardDashboard />} />
        <Route path="/anomalymaster" element={<AnomalyMasterDashboard />} />
        <Route path="/voiceguard" element={<VoiceGuardDashboard />} />
        <Route path="/smartcityguard" element={<SmartCityGuardDashboard />} />
        <Route path="/defiguard" element={<DeFiGuardDashboard />} />
        <Route path="/adversarydefender" element={<AdversaryDefenderDashboard />} />
        <Route path="/sovereignguard" element={<SovereignGuardDashboard />} />
        <Route path="/legacyshield" element={<LegacyShieldDashboard />} />
      </Routes>
      <AIChatBot />
      </main>
    </>
  );
}

export default App;
