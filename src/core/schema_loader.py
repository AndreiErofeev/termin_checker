import json
import logging
from typing import Any

from .database import Database
from .models import Service

logger = logging.getLogger(__name__)


def load_schema_from_s3(s3_client: Any, bucket: str, key: str) -> dict:
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read())


def upsert_services(db: Database, schema: dict) -> int:
    """Insert or update services from schema. Returns count of services processed."""
    count = 0
    departments = schema.get("departments", {})

    with db.get_session() as session:
        for dept_name, dept_data in departments.items():
            base_url = dept_data.get("url", "https://termine.duesseldorf.de/select2?md=3")
            for category, cat_data in dept_data.get("categories", {}).items():
                for service_name in cat_data.get("services", {}):
                    existing = session.query(Service).filter_by(
                        category=category, service_name=service_name
                    ).first()
                    if existing:
                        existing.base_url = base_url
                        existing.active = True
                    else:
                        session.add(Service(
                            category=category,
                            service_name=service_name,
                            base_url=base_url,
                            active=True,
                        ))
                    count += 1

    logger.info("Upserted %d services from schema", count)
    return count


def load_and_sync(db: Database, bucket: str, key: str = "termin/schema.json") -> int:
    """Convenience: fetch from S3 and upsert into DB. Returns service count."""
    import boto3
    s3 = boto3.client("s3")
    schema = load_schema_from_s3(s3, bucket, key)
    return upsert_services(db, schema)
