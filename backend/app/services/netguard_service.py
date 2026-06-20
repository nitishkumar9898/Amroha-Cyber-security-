from sqlalchemy.orm import Session
from ..models.netguard import NetworkNode, TrafficLog, ThreatForecast
from ..schemas.netguard import NodeRegister, TrafficIngestRequest, SimulationRequest
from ..modules.netguard_engine import DLTrafficAnalyzer, TelecomSlicingMonitor, SCADAProtector, APTSimulator

class NetGuardService:
    @staticmethod
    def register_node(db: Session, payload: NodeRegister) -> NetworkNode:
        node = NetworkNode(
            node_name=payload.node_name,
            node_type=payload.node_type,
            ip_address=payload.ip_address
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        return node

    @staticmethod
    def analyze_traffic(db: Session, payload: TrafficIngestRequest) -> dict:
        node = db.query(NetworkNode).filter(NetworkNode.id == payload.node_id).first()
        if not node:
            raise ValueError("Node not found")

        # Routing the analysis based on node type
        if node.node_type == "TELECOM":
            result = TelecomSlicingMonitor.check_slice(payload.protocol, payload.payload_signature)
        elif node.node_type == "SCADA":
            result = SCADAProtector.inspect(payload.protocol, payload.payload_signature)
        else:
            result = DLTrafficAnalyzer.analyze(payload.protocol, payload.bytes_transferred, payload.payload_signature)

        # Log traffic
        log_entry = TrafficLog(
            node_id=node.id,
            protocol=payload.protocol,
            bytes_transferred=payload.bytes_transferred,
            is_anomalous=result["is_anomalous"],
            threat_type=result["threat_type"]
        )
        db.add(log_entry)
        db.commit()

        # TODO: Escalate to ResponseForge if anomalous

        return {
            "node_id": node.id,
            "is_anomalous": result["is_anomalous"],
            "threat_type": result["threat_type"],
            "confidence": result["confidence"]
        }

    @staticmethod
    def simulate_attack(db: Session, payload: SimulationRequest) -> dict:
        node = db.query(NetworkNode).filter(NetworkNode.id == payload.node_id).first()
        if not node:
            raise ValueError("Node not found")

        forecast = APTSimulator.forecast(payload.simulation_type)

        forecast_record = ThreatForecast(
            node_id=node.id,
            predicted_attack_type=payload.simulation_type,
            confidence_score=0.9,
            time_to_impact_hours=forecast["predicted_impact_hours"]
        )
        db.add(forecast_record)
        db.commit()

        return {
            "node_id": node.id,
            "simulation_type": payload.simulation_type,
            "predicted_impact_hours": forecast["predicted_impact_hours"],
            "recommended_action": forecast["recommended_action"]
        }
