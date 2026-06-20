# Compliance Engine package

"""Top-level package for Cyber Law and Compliance module.
Provides rule engine, admissibility checks, audit trails, reporting, and monitoring.
"""

from .config_loader import load_rules_into_engine
from .monitor import engine

# Load compliance rules at import time
load_rules_into_engine(engine)
