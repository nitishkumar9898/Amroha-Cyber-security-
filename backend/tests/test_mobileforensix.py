import pytest
import os
import tempfile
from backend.app.modules.mobile import MobileForensicsParser
from backend.app.modules.chain_of_custody import CustodyLedger
from backend.app.services.mobileforensix_service import mobileforensix_engine

def test_mobile_parser_db_seeding():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_extraction.db")
        # Should seed database since it doesn't exist
        messages = MobileForensicsParser.parse_db_messages(db_path)
        assert len(messages) > 0
        assert messages[0]["sender"] == "APT-Operator-01"
        assert "location" in messages[0]
        assert "latitude" in messages[0]["location"]

def test_hardware_acquisition_edl():
    res = MobileForensicsParser.simulate_hardware_acquisition("DEV_SAMSUNG_S24_982", "EDL")
    assert res["acquisition_success"] is True
    assert "userdata" in [p["name"] for p in res["extracted_partitions"]]
    assert "decryption_level" in res
    assert "USB_D+" in res["hardware_pins_mapped"]

def test_hardware_acquisition_jtag():
    res = MobileForensicsParser.simulate_hardware_acquisition("DEV_IOT_ROUTER_10", "JTAG")
    assert res["acquisition_success"] is True
    assert "TDO" in res["hardware_pins_mapped"]

def test_timeline_reconstruction():
    chat_logs = [
        {"timestamp": "2026-06-19 12:00:00", "sender": "user1", "receiver": "user2", "message": "msg1", "location": {"latitude": 0.0, "longitude": 0.0}},
        {"timestamp": "2026-06-19 10:00:00", "sender": "user2", "receiver": "user1", "message": "msg2", "location": {"latitude": 0.0, "longitude": 0.0}}
    ]
    timeline = MobileForensicsParser.reconstruct_forensic_timeline(chat_logs, "DEV_01")
    assert len(timeline) >= 4
    # Event types included
    event_types = [event["event_type"] for event in timeline]
    assert "CHAT_MESSAGE" in event_types
    assert "CELLULAR_HANDSHAKE" in event_types
    assert "FILE_SYSTEM_WRITE" in event_types
    
    # Chronological sort check (10:00 should precede 12:00)
    chat_events = [e for e in timeline if e["event_type"] == "CHAT_MESSAGE"]
    assert chat_events[0]["timestamp"] == "2026-06-19 10:00:00"
    assert chat_events[1]["timestamp"] == "2026-06-19 12:00:00"

def test_custody_ledger_integrity():
    ledger = CustodyLedger(item_id="ITEM-001", description="Test Device")
    initial_hash = ledger.current_hash
    
    # Transfer custody
    h1 = ledger.record_transfer(
        from_user="Officer_A",
        to_user="Officer_B",
        from_agency="NIA",
        to_agency="CBI",
        rationale="Transfer to lab"
    )
    assert h1 != initial_hash
    assert len(ledger.log) == 1
    assert ledger.log[0]["input_integrity_hash"] == initial_hash
    assert ledger.log[0]["block_integrity_hash"] == h1

    # Transfer again
    h2 = ledger.record_transfer(
        from_user="Officer_B",
        to_user="Lab_Tech_C",
        from_agency="CBI",
        to_agency="Forensics_Lab",
        rationale="Analysis"
    )
    assert h2 != h1
    assert len(ledger.log) == 2
    assert ledger.log[1]["input_integrity_hash"] == h1
    assert ledger.log[1]["block_integrity_hash"] == h2

    # Generate BSA Section 63 certificate
    cert = ledger.generate_bsa_certificate("Lab_Tech_C", "Chief Analyst", "SHA256_EXTRACT_DUMP")
    assert cert["certificate_title"] == "CERTIFICATE UNDER SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM, 2023"
    assert cert["evidence_item"]["raw_image_sha256"] == "SHA256_EXTRACT_DUMP"
    assert cert["ledger_chain_signature"] == h2
    assert cert["signature_status"] == "DIGITALLY_SIGNED_BSA_VALID"

def test_mobileforensix_engine_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "acq.db")
        res = mobileforensix_engine.process_mobile_extraction(
            device_id="DEV_ONEPLUS_11",
            db_path=db_path,
            officer_name="officer_verma",
            agency_name="NIA",
            mode="EDL"
        )
        assert res["forensix_version"] == "1.0.0"
        assert res["device_id"] == "DEV_ONEPLUS_11"
        assert len(res["incident_timeline"]) > 0
        assert len(res["chain_of_custody_history"]) == 1
        assert res["bsa_section_63_compliance"]["signature_status"] == "DIGITALLY_SIGNED_BSA_VALID"
