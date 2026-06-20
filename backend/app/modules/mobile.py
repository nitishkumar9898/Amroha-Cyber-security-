"""
Mobile Forensics Database Parser & Acquisition Simulator
Parses logical extracts (Signal, WhatsApp SQLite db), performs physical/EDL dumps,
and structures timeline event logs across communication, cellular, and cloud syncs.
"""
import sqlite3
import os
import json
import hashlib
from datetime import datetime, timedelta
import random
from typing import Dict, Any, List

class MobileForensicsParser:
    @staticmethod
    def _seed_database(db_filepath: str):
        """Auto-seed a simulated database for local range testing."""
        os.makedirs(os.path.dirname(db_filepath) if os.path.dirname(db_filepath) else ".", exist_ok=True)
        conn = sqlite3.connect(db_filepath)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                latitude REAL,
                longitude REAL
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM messages")
        if cursor.fetchone()[0] == 0:
            base_time = datetime.now() - timedelta(hours=48)
            messages = [
                ("APT-Operator-01", "Suspect-Handler", "Package delivered. Exfiltration complete. Transfer 0.8 BTC.", base_time.strftime("%Y-%m-%d %H:%M:%S"), 28.6139, 77.2090),
                ("Suspect-Handler", "APT-Operator-01", "Initiate Phase-2 target. Avoid detection window.", (base_time + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), 19.0760, 72.8777)
            ]
            cursor.executemany("INSERT INTO messages (sender, receiver, message, timestamp, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)", messages)
        conn.commit()
        conn.close()

    @classmethod
    def parse_db_messages(cls, db_filepath: str) -> List[Dict[str, Any]]:
        """Parses SQLite messaging logs, seeding automatically if missing."""
        if not os.path.exists(db_filepath):
            try:
                cls._seed_database(db_filepath)
            except Exception:
                return []
        try:
            conn = sqlite3.connect(db_filepath)
            cursor = conn.cursor()
            cursor.execute("SELECT id, sender, receiver, message, timestamp, latitude, longitude FROM messages")
            rows = cursor.fetchall()
            messages = []
            for r in rows:
                messages.append({
                    "id": r[0],
                    "sender": r[1],
                    "receiver": r[2],
                    "message": r[3],
                    "timestamp": r[4],
                    "location": {"latitude": r[5], "longitude": r[6]}
                })
            conn.close()
            return messages
        except Exception:
            return []

    @staticmethod
    def simulate_hardware_acquisition(device_id: str, mode: str = "EDL") -> Dict[str, Any]:
        """
        Simulates hardware-level extraction (EDL - Emergency Download, JTAG pinout, chip-off eMMC).
        Calculates decryption status and partition tables.
        """
        seed_hash = int(hashlib.md5(device_id.encode()).hexdigest(), 16)
        
        is_supported = mode in ["EDL", "JTAG", "CHIP_OFF"]
        encryption_status = "File-Based Encryption (FBE) - Decrypted via Keymaster" if (seed_hash % 2 == 0) else "Full-Disk Encryption (FDE) - Decrypted"
        
        partitions = [
            {"name": "boot", "size_kb": 65536, "hash": hashlib.sha256(b"boot").hexdigest()},
            {"name": "system", "size_kb": 2097152, "hash": hashlib.sha256(b"system").hexdigest()},
            {"name": "userdata", "size_kb": 33554432, "hash": hashlib.sha256(b"userdata").hexdigest()}
        ]
        
        return {
            "device_id": device_id,
            "acquisition_mode": mode,
            "acquisition_success": is_supported,
            "decryption_level": encryption_status if is_supported else "LOCKED_ENCRYPTED",
            "extracted_partitions": partitions if is_supported else [],
            "hardware_pins_mapped": ["TDO", "TDI", "TCK", "TMS", "RESET"] if mode == "JTAG" else ["USB_D+", "USB_D-"]
        }

    @staticmethod
    def reconstruct_forensic_timeline(chat_logs: List[Dict[str, Any]], device_id: str) -> List[Dict[str, Any]]:
        """
        AI-powered Timeline Reconstruction: Merges chat messages, network cell tower handshakes,
        GPS tracking points, and system file write events chronologically.
        """
        timeline = []
        base_time = datetime.now() - timedelta(hours=24)
        
        # 1. Inject Chat Messages
        for chat in chat_logs:
            timeline.append({
                "timestamp": chat["timestamp"],
                "event_type": "CHAT_MESSAGE",
                "source": "Signal_Secure_Storage",
                "description": f"Message from {chat['sender']} to {chat['receiver']}: '{chat['message']}'",
                "coordinates": chat["location"]
            })

        # 2. Inject Cellular Tower Handshakes (5G/6G)
        timeline.append({
            "timestamp": (base_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "CELLULAR_HANDSHAKE",
            "source": "Modem_Baseband_Log",
            "description": "Connected to cell tower Jio_5G_Tower_East_Delhi. Signal: -84dBm.",
            "coordinates": {"latitude": 28.6200, "longitude": 77.2150}
        })
        
        # 3. Inject App Network syncs
        timeline.append({
            "timestamp": (base_time + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "CLOUD_SYNC_ESTABLISHED",
            "source": "Google_Drive_Backup_Daemon",
            "description": "Cloud synchronization initiated for account: backup_officer@gmail.com.",
            "coordinates": {"latitude": 28.6139, "longitude": 77.2090}
        })
        
        # 4. Inject System File Modifications
        timeline.append({
            "timestamp": (base_time + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "FILE_SYSTEM_WRITE",
            "source": "OS_Kernel_Auditd",
            "description": "Binary written to /data/user/0/com.secure.chat/files/libpayload.so. Set permissions to executable.",
            "coordinates": {"latitude": 19.0760, "longitude": 72.8777}
        })
        
        # Sort chronologically
        timeline.sort(key=lambda x: x["timestamp"])
        return timeline
