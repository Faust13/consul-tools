import requests
import logging
from models import db, ConsulServices, Dcs


logger = logging
logger.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

def consul_health_check(host: str, port: int): # dummy check what consul is available
    healthcheck_url = 'http://'+host+':'+str(port)+'/v1/status/leader' 
    try:
        healthcheck = requests.get(healthcheck_url)
        if healthcheck.status_code == 200:
            logger.debug('successful connection to host %s:%s', host, port)
    except:
        logger.error('Healthcheck for %s failed! Status code is %s, msg: %s', healthcheck_url, healthcheck.status_code, healthcheck.json)
        raise

def get_acl_token(name: str):
    try:
        record = ConsulServices.query.filter_by(service=name).first()
        token = record.token
        service_id = record.id
    except:
        logger.error('Failed to select token for service %s', name)
    return dict(token = token, id = service_id)

def drop_service(name: str):
    try:
        record = ConsulServices.query.filter_by(service=name).first()
        db.session.delete(record)
        db.session.commit()
    except:
        logger.error('Failed to delete service %s', name)
    return

def add_dc(dc_name: str):
    record = Dcs()
    record.name = dc_name
    db.session.add(record)
    db.session.commit()
    logger.debug('Added new DC: %s', dc_name)

def drop_dc(name: str):
    record = Dcs.query.filter_by(name=name).first()
    db.session.delete(record)
    db.session.commit()



