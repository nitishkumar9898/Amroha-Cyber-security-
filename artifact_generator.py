"""
Artifact Generator for CyberThreatForge
Generates safe, synthetic logs, mock mobile database records, and deepfake metadata
for forensic investigation training.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta

class ForensicArtifactGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_web_access_logs(self, filename="web_access.log", count=20):
        """Generates synthetic Apache-style logs containing mock web attacks (SQLi, Path Traversal)."""
        filepath = os.path.join(self.output_dir, filename)
        base_time = datetime.now() - timedelta(hours=1)
        
        logs = []
        # Normal traffic
        for i in range(count - 5):
            time_str = (base_time + timedelta(seconds=i*30)).strftime("%d/%b/%Y:%H:%M:%S +0000")
            logs.append(f'192.168.1.50 - - [{time_str}] "GET /index.html HTTP/1.1" 200 1043 "http://example.com" "Mozilla/5.0"')
            logs.append(f'192.168.1.51 - - [{time_str}] "GET /styles/main.css HTTP/1.1" 200 4502 "http://example.com" "Mozilla/5.0"')

        # Mock SQL Injection attempts (benign patterns)
        sqli_time = (base_time + timedelta(minutes=15)).strftime("%d/%b/%Y:%H:%M:%S +0000")
        logs.append(f'10.0.2.15 - - [{sqli_time}] "GET /product.php?id=1%20UNION%20SELECT%20NULL,username,password%20FROM%20users HTTP/1.1" 500 290 "http://example.com" "sqlmap/1.4"')

        # Mock Path Traversal attempts
        traversal_time = (base_time + timedelta(minutes=20)).strftime("%d/%b/%Y:%H:%M:%S +0000")
        logs.append(f'10.0.2.15 - - [{traversal_time}] "GET /view.php?file=../../../../etc/passwd HTTP/1.1" 403 150 "-" "Mozilla/5.0"')

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(logs) + "\n")
        
        return filepath

    def generate_mobile_chat_db(self, db_name="chat_history.db"):
        """Generates a mock SQLite database representing mobile forensics artifacts."""
        filepath = os.path.join(self.output_dir, db_name)
        
        # Remove if exists to recreate fresh
        if os.path.exists(filepath):
            os.remove(filepath)
            
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # Create mock tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                receiver TEXT,
                message TEXT,
                timestamp TEXT,
                latitude REAL,
                longitude REAL
            )
        """)
        
        # Insert mock chat records
        chat_data = [
            ("Alice", "Bob", "Hello! Are we meeting today?", "2026-06-19 08:00:00", 28.6139, 77.2090),  # Delhi coords
            ("Bob", "Alice", "Yes, near Connaught Place.", "2026-06-19 08:02:15", 28.6304, 77.2177),
            ("Alice", "Bob", "Perfect. I'll bring the file.", "2026-06-19 08:05:00", 28.6139, 77.2090),
            ("Bob", "Alice", "Received. Let me know when you arrive.", "2026-06-19 08:06:30", 28.6304, 77.2177)
        ]
        
        cursor.executemany("""
            INSERT INTO messages (sender, receiver, message, timestamp, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, chat_data)
        
        conn.commit()
        conn.close()
        
        return filepath

    def generate_deepfake_metadata(self, filename="media_analysis.json"):
        """Generates synthetic forensic analysis metadata report for deepfakes/manipulated media."""
        filepath = os.path.join(self.output_dir, filename)
        
        metadata = {
            "file_name": "evidence_video.mp4",
            "file_size_bytes": 10485760,
            "codec": "h264",
            "frame_rate": 30.0,
            "manipulation_analysis": {
                "face_consistency_score": 0.42,  # Low score indicates high likelihood of manipulation
                "double_compression_detected": True,
                "facial_artifact_coordinates": [
                    {"frame": 120, "x": 340, "y": 200, "confidence": 0.89},
                    {"frame": 121, "x": 342, "y": 201, "confidence": 0.91}
                ],
                "gan_signature_match": "StyleGAN2_Simulated",
                "verdict": "MANIPULATED_MEDIA"
            },
            "exif_data": {
                "Make": "Unknown",
                "Model": "Synthesized",
                "Software": "DeepFaceLab_Simulated",
                "ModifyDate": "2026-06-19 08:12:00"
            }
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        return filepath

    def generate_darkweb_intel(self, filename="darkweb_intel.json"):
        """Generates synthetic intelligence data from simulated Tor marketplace transactions."""
        filepath = os.path.join(self.output_dir, filename)
        
        intel = {
            "marketplace_alias": "ShadowBazaar",
            "onion_domain": "shadowbazaar777x.onion",
            "scraping_timestamp": datetime.now().isoformat(),
            "extracted_posts": [
                {
                    "post_id": "post_991823",
                    "author": "cryptolord_99",
                    "subject": "DB Leak - Financial Services Database Mock",
                    "message_body": "Selling full database dump of bank database. Over 500k customer details. Serious buyers only. ESCROW accepted.",
                    "posted_time": "2026-06-19T02:15:00",
                    "pricing": {
                        "amount_btc": 0.05,
                        "equivalent_usd": 3200
                    },
                    "payment_destination": "bc1qxy2kg3ut7wvuf5vavfecsl7t6sn20agwxadg3d"
                },
                {
                    "post_id": "post_991824",
                    "author": "byte_shifter",
                    "subject": "Zero-Day POC Mock Advisory",
                    "message_body": "Offering proof of concept logic for simulated buffer overflow training.",
                    "posted_time": "2026-06-19T03:40:00",
                    "pricing": {
                        "amount_monero": 12.5,
                        "equivalent_usd": 2100
                    },
                    "payment_destination": "44AFFq5kSiGbG6eUPGdQ4GP6ySbbZ"
                }
            ],
            "forensic_markers": {
                "pgp_public_key_fingerprint": "8F3A 2B6C 1D9E 5F7A 4C3D 2B1A 9E8D 7C6B",
                "coordination_channels": [
                    "t.me/shadowbazaar_support_mock",
                    "element.io/#shadowbazaar:matrix.org"
                ]
            }
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(intel, f, indent=4)
            
        return filepath

