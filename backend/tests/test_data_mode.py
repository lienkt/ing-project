import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.session import Base
from app.models.campaign import Campaign, CampaignDetails
from app.models.catalog import Bank, ProjectOption
from app.models.features import CampaignFeature
from scripts.seed_demo import DemoCampaign, seed_demo
from scripts.setup_demo import move_existing


def test_database_selection_and_separation():
    real = Settings(_env_file=None, data_mode='real')
    demo = Settings(_env_file=None, data_mode='demo')
    assert real.active_database_url == real.database_url
    assert demo.active_database_url == demo.demo_database_url
    assert real.active_database_url != demo.active_database_url
    with pytest.raises(ValidationError):
        Settings(_env_file=None, data_mode='invalid')
    with pytest.raises(ValidationError):
        Settings(_env_file=None, demo_database_url=real.database_url.replace('localhost', '127.0.0.1'))


def test_move_demo_preserves_research_and_label_edits():
    source = create_engine('sqlite://')
    destination = create_engine('sqlite://')
    for engine in (source, destination):
        Base.metadata.create_all(engine)
    url = 'https://example.com/bank-comparison-demo/1'
    with Session(source) as db, db.begin():
        db.add(Bank(name='DEMO — ING', normalized_name='demo — ing'))
        db.add(ProjectOption(key='demo_current_account', name='Demo Current Account'))
        real = Campaign(bank_name='ING', project='current_account', campaign_url='https://example.com/research')
        demo = Campaign(bank_name='DEMO — ING', project='demo_current_account', campaign_url=url)
        demo.details = CampaignDetails(campaign_name='DEMO — Changed title')
        demo.features = CampaignFeature(word_count=1234, labeling_status='Completed', product_name='DEMO — Changed product')
        db.add_all([real, demo])
    assert move_existing(source, destination, [url]) == 1
    with Session(source) as db:
        assert db.scalar(select(func.count()).select_from(Campaign)) == 1
        assert db.scalar(select(Campaign)).campaign_url.endswith('/research')
        assert db.scalar(select(Bank)) is None
    with Session(destination) as db:
        page = db.scalar(select(Campaign))
        assert page.bank_name == 'ING'
        assert page.project == 'current_account'
        assert page.features.word_count == 1234
        assert page.features.labeling_status == 'Completed'
        assert page.features.product_name == 'Changed product'
        assert page.details.campaign_name == 'Changed title'
    assert move_existing(source, destination, [url]) == 0


def test_demo_seed_repeat_preserves_edits():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    rows = TypeAdapter(list[DemoCampaign]).validate_python(json.loads(Path('data/demo_campaigns.json').read_text()))
    with Session(engine) as db, db.begin():
        assert seed_demo(db, rows) == len(rows)
        first = db.scalar(select(Campaign).order_by(Campaign.id))
        first.features.word_count = 999
        db.flush()
        assert seed_demo(db, rows) == 0
        assert first.features.word_count == 999
        assert all(not page.bank_name.startswith('DEMO') for page in db.scalars(select(Campaign)))


def test_auto_demo_examples_preserve_pending_review_and_existing_edits():
    rows = TypeAdapter(list[DemoCampaign]).validate_python(json.loads(
        (Path(__file__).resolve().parents[1] / 'data' / 'demo_campaigns.json').read_text()))
    auto_rows = [row for row in rows if row.auto_stage]
    assert len(auto_rows) == 3
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db, db.begin():
        assert seed_demo(db, auto_rows) == 3
    with Session(engine) as db, db.begin():
        campaigns = {c.bank_name: c for c in db.scalars(select(Campaign))}
        pending = campaigns['ING']
        assert pending.features is None and pending.has_suggestions
        assert pending.source_import.page['is_demo']
        assert pending.proposal.values['word_count'] > 0
        assert campaigns['KBC'].labeling_status == 'In Progress'
        assert campaigns['KBC'].features.source == 'manual_override'
        assert campaigns['Revolut'].labeling_status == 'Completed'
        assert campaigns['Revolut'].proposal.reviewed
        campaigns['KBC'].features.word_count = 12345
    with Session(engine) as db, db.begin():
        assert seed_demo(db, auto_rows) == 0
        assert db.scalar(select(Campaign).where(Campaign.bank_name == 'KBC')).features.word_count == 12345
    engine.dispose()
