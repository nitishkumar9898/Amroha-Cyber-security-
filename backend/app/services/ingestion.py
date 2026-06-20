import os
from google.cloud import pubsub_v1

# Load Pub/Sub topic names from environment or config
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'my-gcp-project')
DEVICE_TOPIC = os.getenv('DATAFORGE_DEVICE_TOPIC', 'dataforge-device')
LOG_TOPIC = os.getenv('DATAFORGE_LOG_TOPIC', 'dataforge-log')
DARKWEB_TOPIC = os.getenv('DATAFORGE_DARKWEB_TOPIC', 'dataforge-darkweb')
PUBLIC_FEED_TOPIC = os.getenv('DATAFORGE_PUBLIC_TOPIC', 'dataforge-public')

publisher = pubsub_v1.PublisherClient()

def _publish(topic_name: str, data: bytes) -> str:
    """Publish raw bytes to a Pub/Sub topic.
    Returns the message ID.
    """
    topic_path = publisher.topic_path(PROJECT_ID, topic_name)
    future = publisher.publish(topic_path, data)
    return future.result()

def ingest_device_message(message_json: str) -> str:
    """Ingest a JSON string from an IoT device.
    The caller should ensure the message is serialized JSON.
    """
    return _publish(DEVICE_TOPIC, message_json.encode('utf-8'))

def ingest_log_line(log_line: str) -> str:
    """Ingest a single line from system logs.
    """
    return _publish(LOG_TOPIC, log_line.encode('utf-8'))

def ingest_darkweb_record(record_json: str) -> str:
    """Ingest a scraped dark‑web record (JSON string)."""
    return _publish(DARKWEB_TOPIC, record_json.encode('utf-8'))

def ingest_public_feed(record_json: str) -> str:
    """Ingest a public‑feed record (JSON string)."""
    return _publish(PUBLIC_FEED_TOPIC, record_json.encode('utf-8'))
