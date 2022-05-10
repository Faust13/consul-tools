from consul_agent import add_new_service_token, automatic_check_mt, switch_app_mt, switch_dc
from models import Dcs, db, ServicesChecks, ConsulServices
from flask import Flask, render_template, redirect, url_for, session, request, jsonify, Response
from helpers import drop_dc, drop_service, get_acl_token, logger, add_dc
from flask_oauthlib.client import OAuth
from flask_migrate import Migrate
from settings import *
from flask_apscheduler import APScheduler

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
app.config.from_object('settings')
db.init_app(app)
#db.drop_all(app=app)
db.create_all(app=app)
migrate = Migrate(app, db)
app.secret_key = 'development'
oauth = OAuth(app)
scheduler = APScheduler()
scheduler.init_app(app)

 
gitlab = oauth.remote_app(OAUTH_APP_NAME,
    base_url=GITLAB_HOST+'/api/v4/',
    request_token_url=None,
    access_token_url=GITLAB_HOST+'/oauth/token',
    authorize_url=GITLAB_HOST+'/oauth/authorize',
    access_token_method='POST',
    consumer_key=GITLAB_CLIENT_ID,
    consumer_secret=GITLAB_CLIENT_SECRET
)

@scheduler.task('interval', seconds=CONSUL_SCRAPE_INTERVAL)
def autocheck_services():
    with app.app_context():
        service_list = ConsulServices.query.all()
        for service in service_list:
            automatic_check_mt(service.token, service.id)

scheduler.start()

def read_cookies(): #fill variable 'user' with values of cookies
    user = {
        'username': request.cookies.get('username'),
        'name': request.cookies.get('name'),
        'avatar': request.cookies.get('avatar'), 
        'email': request.cookies.get('email')
    }
    return user
 
@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        if 'gitlab_token' in session:
            gitlab_data = gitlab.get('user').data #get info about authnetificated user
            if 'error' in gitlab_data: # check token for experitaion and send user to re-auth
                logger.error( 'Access denied: reason=%s error=%s',
                gitlab_data['error'],
                gitlab_data['error_description'])
                return redirect(url_for('logout'))
            response = redirect(url_for('switcher'))
            #Save info about user to cookies
            response.set_cookie('username', gitlab_data['username']) 
            response.set_cookie('name', gitlab_data['name'])
            response.set_cookie('avatar', gitlab_data['avatar_url'])
            response.set_cookie('email', gitlab_data['email'])
            return response
        return redirect(url_for('login_page'))


@app.route('/switcher', methods=['GET'])
def switcher():
    if request.method == 'GET':
        if 'gitlab_token' in session:
            user = read_cookies()
            return render_template('index.html', user=user)
        return redirect(url_for('login_page'))

#######################################
######## SWITCHER #####################
#######################################
@app.route('/switcher/dc', methods=['GET'])
def switcher_dc():
    if request.method == 'GET':
        if 'gitlab_token' in session:
            user = read_cookies()
            checks_list = ServicesChecks.query.all()
            dc_list = Dcs.query.all()
            print(dc_list)
            print(checks_list)
            return render_template('mt_switch_dc_scope.html', dc_list=dc_list, checks_list=checks_list, user=user)
        return redirect(url_for('login_page'))

@app.route('/switcher/services', methods=['GET'])
def switcher_services():
    if request.method == 'GET':
        if 'gitlab_token' in session:
            user = read_cookies()
            checks_list = ServicesChecks.query.all()
            service_list = ConsulServices.query.all()
            dc_list = Dcs.query.all()
            return render_template('mt_switch_service_scope.html', dc_list=dc_list, checks_list=checks_list, service_list=service_list, user=user)
        return redirect(url_for('login_page'))

@app.route('/settings', methods=['GET'])
def settings():
    if request.method == 'GET':
        if 'gitlab_token' in session:
            user = read_cookies()    
            service_list = ConsulServices.query.all()
            dc_list = Dcs.query.all()
            return render_template('settings.html', service_list=service_list, dc_list=dc_list, user=user)
        return redirect(url_for('login_page'))

@app.route('/test', methods=['GET'])
def test():
    if request.method == 'GET':
        if 'gitlab_token' in session:
            service_list = ConsulServices.query.all()
            for service in service_list:
                automatic_check_mt(service.token, service.id)
                print('lol')
            return "Hello"
        return redirect(url_for('login_page'))

#################################################
################# notAPI ########################
#################################################

@app.route('/api/v1', methods=['GET'])
def api_v1():
    return Response("{'Status':'Ok'}", status=200, mimetype='application/json')

@app.route('/notapi/v1/add/dc', methods=['POST'])
def add_datacenter():
    name = request.form['dc_name']
    add_dc(name)
    return redirect(url_for('settings')) 

@app.route('/notapi/v1/add/service', methods=['POST'])
def add_service():
    service = request.form['service_name']
    token = request.form['acl_token']
    add_new_service_token(token, service)
    return redirect(url_for('settings'))

@app.route('/notapi/v1/delete/service', methods=['POST'])
def del_service():
    service_to_delete = request.form['remove_acl']
    logger.debug(service_to_delete)
    drop_service(service_to_delete)
    return redirect(url_for('settings'))

@app.route('/notapi/v1/delete/dc', methods=['POST'])
def del_dc():
    dc_to_delete = request.form['remove_dc']
    logger.debug(dc_to_delete)
    drop_dc(dc_to_delete)
    return redirect(url_for('settings'))

@app.route('/notapi/v1/switch/job', methods=['POST'])
def switch_job():
    user = read_cookies()
    data = request.form['switch_mt']
    data_splitted = data.split()
    service_name = data_splitted[0]
    dc_id = data_splitted[1]
    service_data = get_acl_token(service_name)
    logger.debug('Service_data variable == is %s', service_data)
    switch_app_mt(service_data['token'], service_name, service_data['id'], dc_id,  user['name'])
    logger.debug('Switch status for service %s in dc %s', service_name, dc_id)
    return redirect(url_for('switcher_services'))

@app.route('/notapi/v1/switch/dc_job', methods=['POST'])
def switch_dc_job():
    user = read_cookies()
    data = request.form['switch_dc_mt']
    switch_dc(data, user['name'])
    return redirect(url_for('switcher_dc'))

#################################################
################ Gitlab OAuth ###################
#################################################

@app.route('/loginpage')
def login_page():
    return render_template('login.html')

@app.route('/login')
def login():
    return gitlab.authorize(callback=url_for('authorized', _external=True, _scheme='http'))
 
 
@app.route('/logout')
def logout():
    del session['gitlab_token']
    return redirect(url_for('login_page'))
 
@app.route('/login/authorized')
def authorized():
    resp = gitlab.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    session['gitlab_token'] = (resp['access_token'], '')
    return redirect(url_for('index'))
 
@gitlab.tokengetter
def get_gitlab_oauth_token():
    return session.get('gitlab_token')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')