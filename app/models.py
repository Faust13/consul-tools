from email.policy import default
from flask_sqlalchemy import SQLAlchemy

# create a new SQLAlchemy object 

db = SQLAlchemy()

# Base model that for other models to inherit from 
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
 

class ServicesChecks(Base):
    __tablename__ = 'service_checks'
    service_id = db.Column(db.Integer, db.ForeignKey('consul_services.id'),
        nullable=False)
    dc_id = db.Column(db.Integer, db.ForeignKey('dcs.id'),
        nullable=False)
    maintance = db.Column(db.Boolean)
    last_update = db.Column(db.DateTime, default=db.func.current_timestamp())
    changed_by = db.Column(db.String(100), nullable=False, default='system') 
    last_scrape = db.Column(db.DateTime, default=db.func.current_timestamp())

class ConsulServices(Base):
    __tablename__ = 'consul_services'
    service = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(100), nullable=False)
    checks = db.relationship('ServicesChecks', backref='consul_services', lazy=True, cascade='delete')

class Dcs(Base):
    __tablename__ = 'dcs'
    name = db.Column(db.String(5), nullable=False)
    checks = db.relationship('ServicesChecks', backref='dcs', lazy=True, cascade='delete') 

