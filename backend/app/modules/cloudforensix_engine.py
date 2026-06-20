import random
from typing import Dict, Any, List

class MultiCloudLogAnalyzer:
    """Simulates AI/Rule-based parsing of AWS/Azure/GCP logs."""
    
    @staticmethod
    def analyze(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        anomalies_detected = 0
        findings = []

        for log in logs:
            event_name = log.get("eventName", "").lower()
            region = log.get("region", "us-east-1")
            
            is_anomalous = False
            score = 0.1
            finding = ""

            # Simulated Rule-Based Anomalies
            if "delete" in event_name and "trail" in event_name:
                is_anomalous = True
                score = 0.95
                finding = "Evasion detected: CloudTrail deletion attempt."
            elif "createuser" in event_name and region not in ["us-east-1", "eu-west-1"]:
                is_anomalous = True
                score = 0.85
                finding = f"Suspicious IAM creation in non-standard region: {region}"
            elif log.get("sourceIpAddress") == "185.x.x.x": # Mock TOR/Malicious IP
                is_anomalous = True
                score = 0.99
                finding = "Access from known malicious IP pool."
                
            if is_anomalous:
                anomalies_detected += 1
                findings.append(finding)
                
            results.append({
                "log": log,
                "is_anomalous": is_anomalous,
                "score": score,
                "finding": finding
            })
            
        return {
            "analyzed_count": len(logs),
            "anomalies_detected": anomalies_detected,
            "findings": findings,
            "results": results
        }

class OrchestrationScanner:
    """Simulates K8s and Container image forensics."""
    
    @staticmethod
    def scan(image_hash: str, namespace: str) -> Dict[str, Any]:
        # Mock logic
        is_malicious = "bad" in image_hash.lower()
        
        vulnerabilities = ["CVE-2021-3156 (Sudo Privesc)"] if is_malicious else ["None detected"]
        escape = is_malicious and namespace == "kube-system"
        
        return {
            "image_hash": image_hash,
            "escape_detected": escape,
            "vulnerabilities": vulnerabilities
        }

class ServerlessTracer:
    """Simulates tracing of Lambda / Azure Functions."""
    
    @staticmethod
    def trace(function_name: str) -> Dict[str, Any]:
        path = [f"API_Gateway -> {function_name}"]
        malicious = False
        
        if "crypto" in function_name.lower() or "miner" in function_name.lower():
            path.append(f"{function_name} -> outbound connection to mining pool")
            malicious = True
        else:
            path.append(f"{function_name} -> DynamoDB / S3")
            
        return {
            "function_name": function_name,
            "execution_path": path,
            "malicious_payload_detected": malicious
        }

class DataResidencyChecker:
    """Simulates checking cross-region data transfers."""
    
    @staticmethod
    def check(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        violations = []
        for log in logs:
            if log.get("eventName") == "S3Transfer" and log.get("sourceRegion") == "eu-central-1" and log.get("destRegion") == "us-east-1":
                violations.append("GDPR Violation: Data transferred from EU to US.")
                
        return {
            "is_compliant": len(violations) == 0,
            "violations": violations
        }
