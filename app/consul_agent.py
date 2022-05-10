import consul
from helpers import logger, consul_health_check
from settings import CONSUL_PORT, CONSUL_HOST
from models import db, ServicesChecks, Dcs, ConsulServices


def consul_check_mt(consul_token: str, service_name: str, service_dc: str):
    key_path = 'service/'+service_name+'/dc/'+service_dc+'/maintenance'
    try:
        c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT, token=consul_token)
        data = c.kv.get(key_path)
        current_status = data[1]['Value'].decode('utf-8')
        logger.info('Got key from consul! Current status is %s', current_status)
    except:
        logger.info('Key %s doesnt found', key_path)
        raise
    logger.info('Maintance for service %s in datacenter %s is %s', service_name, service_dc, current_status)
    mt = True if current_status == 'on' else False
    return mt

def get_app_mt(consul_token: str, service_id: int, dc_name: str, dc_id: int): #get value for key /service/$name/dc/$dc/maintanice 
    service_name = ConsulServices.query.filter_by(id=service_id).first().service 
    consul_health_check(CONSUL_HOST, CONSUL_PORT)
    mt=consul_check_mt(consul_token, service_name, dc_name)
    try:
        record = ServicesChecks.query.filter_by(service_id=service_id, dc_id=dc_id).first()
        record.last_scrape = db.func.current_timestamp()
        if record.maintance != mt:
            record.maintance = mt
            record.last_update = db.func.current_timestamp()
            record.changed_by = 'system'
        db.session.commit()
    except:
        logger.error('Cannot add new record to db. Service: %s dc: %s', service_id, dc_name)
        raise
    return logger.debug('Database record for service %s in datacenter %s is updated', service_id, dc_name)


def switch_app_mt(consul_token: str, service_name: str, service_id: int, datacenter_id: int, username: str):
    try:
        service_dc = Dcs.query.filter_by(id=datacenter_id).first().name
        mt = consul_check_mt(consul_token, service_name, service_dc)
    except:
        logger.error('Cannot get current status!')
        raise
    if mt == False:
        new_status = 'on'
        status_message = 'is out of balancing'
    elif mt == True:
        new_status = 'off'
        status_message = 'is ready to accept connections again'
    else:
        try:
            logger.warning('Incorrect status value = %s, will be overwriten with "on"', mt)
            new_status = 'on'
            status_message = 'now is out of balancing'
            pass
        except:
            logger.error('Fatal error')
            raise

    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT, token=consul_token)
    key_path = 'service/'+service_name+'/dc/'+service_dc+'/maintenance'
    c.kv.put(key_path, new_status)
    get_app_mt(consul_token, service_id, service_dc, datacenter_id)
    record = ServicesChecks.query.filter_by(service_id=service_id, dc_id=datacenter_id).first()
    if record.maintance != mt:
        record.last_update = db.func.current_timestamp()
        record.changed_by = username
        db.session.commit()

    return logger.debug('Datacenter %s %s', service_dc, status_message)

def automatic_check_mt(consul_token: str, service_id: int):
    datacenters = Dcs.query.all()
    for datacenter in datacenters:
       get_app_mt(consul_token, service_id, datacenter.name, datacenter.id)


def add_new_service_token(acl_token: str, name: str):
    try:
            record = ConsulServices()
            record.token = acl_token
            record.service = name
            db.session.add(record)
            db.session.commit()
            db.session.refresh(record)
            register_new_service(acl_token, record.id, name)
    except:
        logger.error('Failed to save service %s with acl_token %s', name, acl_token)
    return

def register_new_service(consul_token: str, service_id: int, service_name: str): #add new records to db when register service 
    datacenters = Dcs.query.all()
    for datacenter in datacenters:
        #consul_health_check(CONSUL_HOST, CONSUL_PORT)
        logger.debug('Starting add new service with id %s in dc %s', service_id, datacenter.name)
        mt=consul_check_mt(consul_token, service_name, datacenter.name)
        logger.debug('Mt check for new service with id %s in dc %s passed!', service_id, datacenter.name)
        try:
            record = ServicesChecks()
            record.service_id = service_id
            record.maintance = mt
            record.dc_id = datacenter.id
            db.session.add(record)
            db.session.commit()
            logger.debug('Database record for service with id %s in datacenter %s is created', service_id, datacenter)
        except:
            logger.error('ERROR!')
            raise

def switch_dc(dc_id: int, username: str):
    jobs = ServicesChecks.query.filter_by(dc_id=dc_id).all()
    for job in jobs:
        data = ConsulServices.query.filter_by(id=job.service_id).first()
        acl_key = data.token
        service_name = data.service
        service_id = job.service_id
        logger.debug('Starting switch for dc id: %s, service: %s, acl_key: %s. Current state is %s', dc_id, service_name, acl_key, job.maintance)
        switch_app_mt(acl_key, service_name, service_id, dc_id, username)
