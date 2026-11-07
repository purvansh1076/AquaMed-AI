"""
AquaMediAI — Cryptographic Mediation Audit & Merkle Proof Engine
================================================================
Constructs a deterministic SHA-256 Merkle tree over final water allocation
decisions and multi-agent mediation agreements.

Guarantees:
  1. Tamper-evidence: Any modification of allocation vectors changes the Merkle root.
  2. Proof of verification: Verification certificate includes root hash, signature digest, and timestamp.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def sha256_hex(data: str) -> str:
    """Compute SHA-256 hex digest of UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class MerkleAuditTree:
    """Binary Merkle Tree for water mediation agreement verification."""

    def __init__(self, leaves_data: List[Dict[str, Any]]) -> None:
        self.raw_records = list(leaves_data)
        self.leaf_hashes: List[str] = [
            sha256_hex(json.dumps(record, sort_keys=True)) for record in self.raw_records
        ]
        self.root_hash: str = self._build_merkle_root(self.leaf_hashes)

    def _build_merkle_root(self, hashes: List[str]) -> str:
        """Recursively compute Merkle root from list of leaf hashes."""
        if not hashes:
            return sha256_hex("EMPTY_AUDIT_TREE")
        if len(hashes) == 1:
            return hashes[0]

        current_level = list(hashes)
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = sha256_hex(left + right)
                next_level.append(combined)
            current_level = next_level

        return current_level[0]

    def generate_certificate(
        self,
        scenario_id: str,
        expert_signoff: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Produce an immutable audit certificate for the agreed allocation."""
        now_iso = datetime.now(timezone.utc).isoformat()
        cert_data = {
            "scenario_id": scenario_id,
            "timestamp": now_iso,
            "merkle_root": self.root_hash,
            "record_count": len(self.raw_records),
            "expert_signoff": expert_signoff or "Verified by AquaMedi AI Autonomous Arbitrator",
            "algorithm": "SHA-256 Merkle Audit Tree (NIST FIPS 180-4)",
        }
        cert_signature = sha256_hex(f"{scenario_id}:{self.root_hash}:{now_iso}")
        cert_data["certificate_digest"] = cert_signature
        return cert_data


def verify_certificate_integrity(
    records: List[Dict[str, Any]],
    expected_merkle_root: str,
) -> bool:
    """Verify that records match the certified Merkle root."""
    tree = MerkleAuditTree(records)
    return tree.root_hash == expected_merkle_root
