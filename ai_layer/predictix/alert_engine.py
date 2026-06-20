# Predictix alert engine
import smtplib
import json
from email.mime.text import MIMEText
from pathlib import Path

# Load alert configuration (thresholds, recipients) from a JSON/YAML file
def load_alert_config(config_path: str = "config/predictix_alerts.json"):
    if not Path(config_path).exists():
        # default config
        return {
            "risk_threshold": 0.7,
            "email": {
                "enabled": False,
                "smtp_server": "smtp.example.com",
                "port": 587,
                "username": "alert@example.com",
                "password": "secret",
                "recipients": ["security@example.com"]
            },
            "slack": {
                "enabled": False,
                "webhook_url": "https://hooks.slack.com/services/..."
            }
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def send_email(subject: str, body: str, cfg: dict):
    if not cfg.get("enabled"):
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = cfg["username"]
    msg["To"] = ", ".join(cfg["recipients"])
    with smtplib.SMTP(cfg["smtp_server"], cfg["port"]) as server:
        server.starttls()
        server.login(cfg["username"], cfg["password"])
        server.send_message(msg)

def post_to_slack(message: str, cfg: dict):
    if not cfg.get("enabled"):
        return
    import requests
    requests.post(cfg["webhook_url"], json={"text": message})

def evaluate_and_alert(forecast_result: dict):
    """Evaluate risk score against thresholds and emit alerts.
    `forecast_result` should contain keys `risk_score` and `allocation`.
    """
    cfg = load_alert_config()
    risk = forecast_result.get("risk_score", 0)
    if risk >= cfg.get("risk_threshold", 0.7):
        subject = f"[Predictix] High Risk Forecast: {risk:.2f}"
        body = f"Predictix generated a high risk score of {risk:.2f}.\n\nAllocation suggestions:\n{json.dumps(forecast_result.get('allocation'), indent=2)}"
        # Email alert
        send_email(subject, body, cfg.get("email", {}))
        # Slack alert
        post_to_slack(body, cfg.get("slack", {}))
        # Return a dict suitable for persisting as an Alert model
        return {
            "severity": "high",
            "message": body,
        }
    return None
