import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class EvidenceStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or os.path.join(DB_DIR, "blockchain_ledge.db")
        self._local = threading.local()
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_schema()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_schema(self) -> None:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp REAL NOT NULL,
                data_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                nonce INTEGER DEFAULT 0,
                merkle_root TEXT DEFAULT '',
                signature TEXT DEFAULT '',
                chain_of_custody_hash TEXT DEFAULT '',
                block_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                block_index INTEGER NOT NULL,
                data_hash TEXT NOT NULL,
                ts REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                chain_of_custody TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (block_index) REFERENCES blocks(block_index)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                evidence_id TEXT,
                block_index INTEGER,
                actor TEXT DEFAULT 'system',
                details TEXT DEFAULT '{}',
                timestamp TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS case_metadata (
                case_id TEXT PRIMARY KEY,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_evidence_case_id ON evidence(case_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_data_hash ON evidence(data_hash);
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def _normalize_block(block: dict[str, Any]) -> dict[str, Any]:
        norm = dict(block)
        if "block_index" in norm and "index" not in norm:
            norm["index"] = norm.pop("block_index")
        if "index" in norm and "block_index" not in norm:
            norm["block_index"] = norm["index"]
        if "block_hash" in norm and "hash" not in norm:
            norm["hash"] = norm.pop("block_hash")
        if "hash" in norm and "block_hash" not in norm:
            norm["block_hash"] = norm["hash"]
        return norm

    def store_block(self, block: dict[str, Any]) -> None:
        b = self._normalize_block(block)
        self._conn.execute("""
            INSERT OR REPLACE INTO blocks
                (block_index, timestamp, data_hash, prev_hash, nonce, merkle_root,
                 signature, chain_of_custody_hash, block_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            b["index"], b["timestamp"], b["data_hash"],
            b["prev_hash"], b.get("nonce", 0),
            b.get("merkle_root", ""), b.get("signature", ""),
            b.get("chain_of_custody_hash", ""), b["hash"],
        ))
        self._conn.commit()

    def store_blocks(self, blocks: list[dict[str, Any]]) -> None:
        for block in blocks:
            self.store_block(block)

    def get_block(self, index: int) -> Optional[dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM blocks WHERE block_index = ?", (index,)
        ).fetchone()
        return self._normalize_block(dict(row)) if row else None

    def get_all_blocks(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM blocks ORDER BY block_index ASC"
        ).fetchall()
        return [self._normalize_block(dict(r)) for r in rows]

    def chain_length(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM blocks"
        ).fetchone()
        return row["cnt"] if row else 0

    def store_evidence(
        self,
        evidence_id: str,
        case_id: str,
        block_index: int,
        data_hash: str,
        ts: float,
        metadata: Optional[dict[str, Any]] = None,
        chain_of_custody: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        self._conn.execute("""
            INSERT OR REPLACE INTO evidence
                (evidence_id, case_id, block_index, data_hash, ts,
                 metadata, chain_of_custody)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            evidence_id, case_id, block_index, data_hash, ts,
            json.dumps(metadata or {}, default=str),
            json.dumps(chain_of_custody or [], default=str),
        ))
        self._conn.commit()

    def get_evidence(self, evidence_id: str) -> Optional[dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,)
        ).fetchone()
        if row:
            result = dict(row)
            result["metadata"] = json.loads(result.get("metadata", "{}"))
            result["chain_of_custody"] = json.loads(result.get("chain_of_custody", "[]"))
            return result
        return None

    def query_evidence_by_case(self, case_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM evidence WHERE case_id = ? ORDER BY ts DESC",
            (case_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d.get("metadata", "{}"))
            d["chain_of_custody"] = json.loads(d.get("chain_of_custody", "[]"))
            results.append(d)
        return results

    def query_evidence_by_date_range(
        self, start: str, end: str
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM evidence WHERE ts >= ? AND ts <= ? ORDER BY ts ASC",
            (start, end),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["metadata"] = json.loads(d.get("metadata", "{}"))
            d["chain_of_custody"] = json.loads(d.get("chain_of_custody", "[]"))
            results.append(d)
        return results

    def log_audit(
        self,
        action: str,
        evidence_id: Optional[str] = None,
        block_index: Optional[int] = None,
        actor: str = "system",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self._conn.execute("""
            INSERT INTO audit_log (action, evidence_id, block_index, actor, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            action, evidence_id, block_index, actor,
            json.dumps(details or {}, default=str),
        ))
        self._conn.commit()

    def get_audit_log(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d.get("details", "{}"))
            results.append(d)
        return results

    def get_audit_log_by_action(self, action: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM audit_log WHERE action = ? ORDER BY id DESC",
            (action,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d.get("details", "{}"))
            results.append(d)
        return results

    def store_case_metadata(self, case_id: str, metadata: dict[str, Any]) -> None:
        self._conn.execute("""
            INSERT OR REPLACE INTO case_metadata (case_id, metadata)
            VALUES (?, ?)
        """, (case_id, json.dumps(metadata, default=str)))
        self._conn.commit()

    def get_case_metadata(self, case_id: str) -> Optional[dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM case_metadata WHERE case_id = ?", (case_id,)
        ).fetchone()
        if row:
            d = dict(row)
            d["metadata"] = json.loads(d.get("metadata", "{}"))
            return d
        return None

    def export_to_json(self, output_path: Optional[str] = None) -> str:
        blocks = self.get_all_blocks()
        evidence_list = self._conn.execute(
            "SELECT * FROM evidence ORDER BY ts ASC"
        ).fetchall()
        cases = self._conn.execute(
            "SELECT * FROM case_metadata"
        ).fetchall()
        audit = self._conn.execute(
            "SELECT * FROM audit_log ORDER BY id ASC"
        ).fetchall()

        export = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "module": "blockchain-ledge",
            "version": "1.0.0",
            "summary": {
                "block_count": len(blocks),
                "evidence_count": len(evidence_list),
                "audit_entries": len(audit),
            },
            "blocks": blocks,
            "evidence": [dict(e) for e in evidence_list],
            "cases": [dict(c) for c in cases],
            "audit_log": [dict(a) for a in audit],
        }

        output = output_path or os.path.join(
            os.path.dirname(self._db_path), "ledger_export.json"
        )
        with open(output, "w") as f:
            json.dump(export, f, indent=2, default=str)
        return output

    def clear(self) -> None:
        self._conn.executescript("""
            DELETE FROM blocks;
            DELETE FROM evidence;
            DELETE FROM audit_log;
            DELETE FROM case_metadata;
        """)
        self._conn.commit()
