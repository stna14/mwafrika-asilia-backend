"""Sponsors tests use isolated SQLite only, never the existing MySQL database."""
import sys
from pathlib import Path
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.core.database import Base,get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.features.admin_auth.models import AdminUser
from app.features.media_library.models import MediaFile
from app.features.sponsors.models import Sponsor
from app.features.sponsors.router import admin_router,public_router
from app.features.media_library.router import router as media_router

@compiles(BigInteger,'sqlite')
def integer(_t,_c,**kw):return 'INTEGER'

@pytest.fixture
def system(monkeypatch):
    monkeypatch.setattr(settings,'JWT_SECRET','isolated-sponsors-test-key')
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    @event.listens_for(engine,'connect')
    def foreign_keys(connection,_):connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for i,role in enumerate(['super_admin','editor','finance'],1):db.add(AdminUser(id=i,full_name='QA',email=f'qa{i}@example.com',role=role,password_hash='no-real-password',is_active=True))
        db.add(MediaFile(id=1,public_id='qa-logo',original_filename='qa.png',stored_filename='qa.png',url='http://127.0.0.1:8000/uploads/qa.png',mime_type='image/png',size_bytes=1))
        db.add(MediaFile(id=2,public_id='qa-svg',original_filename='unsafe.svg',stored_filename='unsafe.svg',url='/uploads/unsafe.svg',mime_type='image/svg+xml',size_bytes=1))
        db.commit()
    app=FastAPI()
    for router in [admin_router,public_router,media_router]:app.include_router(router)
    def database():
        with Session(engine) as db:yield db
    app.dependency_overrides[get_db]=database
    with TestClient(app) as client:yield client,engine
    engine.dispose()

def auth(i=1):return {'Authorization':'Bearer '+create_access_token(i)}
def create(client,**fields):return client.post('/api/admin/sponsors',headers=auth(),json={'name':'QA Sponsor','logo_media_id':1,**fields})

def test_publication_order_activation_and_crud(system):
    c,e=system
    a=create(c,display_order=2);assert a.status_code==201,a.text
    b=create(c,name='QA First',display_order=1,publish_status='published');assert b.status_code==201
    assert [r['id'] for r in c.get('/api/sponsors').json()['items']]==[b.json()['id']]
    aid=a.json()['id'];bid=b.json()['id']
    assert c.patch(f'/api/admin/sponsors/{aid}',headers=auth(),json={'publish_status':'published'}).status_code==200
    public=c.get('/api/sponsors').json()['items'];assert [r['id'] for r in public]==[bid,aid]
    assert 'logo_media_id' not in public[0] and 'is_active' not in public[0]
    assert c.patch(f'/api/admin/sponsors/{bid}',headers=auth(),json={'is_active':False}).status_code==200
    assert len(c.get('/api/sponsors').json()['items'])==1
    assert c.patch(f'/api/admin/sponsors/{aid}',headers=auth(),json={'publish_status':'draft'}).status_code==200
    assert c.get('/api/sponsors').json()['items']==[]
    assert c.get(f'/api/admin/sponsors/{aid}',headers=auth()).json()['publish_status']=='draft'
    assert c.delete(f'/api/admin/sponsors/{aid}',headers=auth()).status_code==204
    assert c.get(f'/api/admin/sponsors/{aid}',headers=auth()).status_code==404

@pytest.mark.parametrize('fields',[{'website_url':'javascript:alert(1)'},{'website_url':'https://user:password@example.com'},{'name':' '},{'logo_media_id':2},{'logo_media_id':999},{'display_order':-1},{'display_order':True},{'logo_media_id':None,'publish_status':'published'}])
def test_invalid_sponsors_rejected(system,fields):
    c,e=system;assert create(c,**fields).status_code==422
    with Session(e) as db:assert db.query(Sponsor).count()==0

def test_roles_conflict_and_reference_protection(system):
    c,e=system
    assert c.get('/api/admin/sponsors').status_code==401
    for i in [2,3]:assert c.get('/api/admin/sponsors',headers=auth(i)).status_code==403
    row=create(c).json();sid=row['id']
    assert c.patch(f'/api/admin/sponsors/{sid}',headers=auth(),json={'name':'changed','expected_updated_at':'2000-01-01T00:00:00'}).status_code==409
    assert c.patch(f'/api/admin/sponsors/{sid}',headers=auth(),json={'name':None}).status_code==422
    assert c.delete('/api/admin/media/1',headers=auth()).status_code==409
    assert c.get('/api/admin/media/1',headers=auth()).status_code==200

def test_missing_schema_honest_unavailable(system):
    c,e=system;Sponsor.__table__.drop(e)
    assert c.get('/api/sponsors').status_code==503
    assert c.get('/api/admin/sponsors',headers=auth()).status_code==503
