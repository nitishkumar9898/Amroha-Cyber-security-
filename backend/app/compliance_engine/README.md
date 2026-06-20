# Compliance Engine README

## Overview

The **Compliance Engine** provides a modular framework for legal admissibility checking, real‑time compliance monitoring, immutable audit trails, and automated report generation for the CyberThreatForge platform.

### Key Components

- **Rule Engine** (`rule_engine.py`): Define and evaluate compliance rules.
- **Admissibility Checker** (`admissibility_checker.py`): Concrete checks for Indian IT Act 2000 and DPDP 2023.
- **Audit Trail** (`audit_trail.py`): Append‑only log for forensic actions.
- **Monitor** (`monitor.py`): Central event hub that records actions and triggers rule evaluation.
- **Report Generator** (`report_generator.py` + Jinja2 templates): Produce HTML/PDF compliance reports.
- **Models** (`models/`): Dataclasses for `Evidence`, `AuditEntry`, and optional `ComplianceRule`.
- **Configuration** (`config/compliance.yaml`): Declarative rule definitions and ledger/report settings.

### Integration

Existing forensic modules import `record_event` from `compliance_engine.monitor` to automatically log actions and evaluate compliance rules.

### Usage Example

```python
from compliance_engine.admissibility_checker import is_admissible
from compliance_engine.models.evidence import Evidence

e = Evidence(
    id="e1",
    description="Captured network traffic",
    collection_method="forensic_tool",
    source="/data/traffic.pcap",
    timestamp="2026-06-19T12:00:00Z",
    has_consent=True,
)

print(is_admissible(e.__dict__))  # -> True
```

Refer to the source code for detailed APIs.
