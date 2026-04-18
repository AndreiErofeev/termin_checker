import json
from unittest.mock import MagicMock, patch
from src.core.schema_loader import load_schema_from_s3, upsert_services
from src.core.database import Database
from src.core.models import Service


SAMPLE_SCHEMA = {
    "departments": {
        "Dept A": {
            "url": "https://termine.duesseldorf.de/select2?md=4",
            "categories": {
                "Cat 1": {
                    "services": {
                        "Service X": {"max_quantity": 2},
                        "Service Y": {"max_quantity": 1},
                    }
                }
            },
        }
    }
}


def test_load_schema_from_s3():
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=lambda: json.dumps(SAMPLE_SCHEMA).encode())
    }
    result = load_schema_from_s3(mock_s3, "my-bucket", "termin/schema.json")
    assert result["departments"]["Dept A"]["url"] == "https://termine.duesseldorf.de/select2?md=4"


def test_upsert_services_creates_rows():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    upsert_services(db, SAMPLE_SCHEMA)
    with db.get_session() as session:
        services = session.query(Service).all()
    assert len(services) == 2
    names = {s.service_name for s in services}
    assert "Service X" in names
    assert "Service Y" in names


def test_upsert_services_sets_base_url():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    upsert_services(db, SAMPLE_SCHEMA)
    with db.get_session() as session:
        svc = session.query(Service).filter_by(service_name="Service X").first()
    assert svc.base_url == "https://termine.duesseldorf.de/select2?md=4"
    assert svc.category == "Cat 1"


def test_upsert_services_idempotent():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    upsert_services(db, SAMPLE_SCHEMA)
    upsert_services(db, SAMPLE_SCHEMA)  # second call must not duplicate
    with db.get_session() as session:
        count = session.query(Service).count()
    assert count == 2
