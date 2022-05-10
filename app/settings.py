import os

DB_CONF = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'consul-switcher'),
    'username': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASS', 'postgres')
}

MODULES = {
    'consul_mt': os.environ.get('CONSUL_MT_MODULE', True),
    'patroni': os.environ.get('PATRONI_MODULE', True),
    'gitlab_ouath': os.environ.get('GITLAB_OAUTH_MODULE', True), 
}

conn_string ='postgresql+psycopg2://'+DB_CONF['username']+':'+DB_CONF['password']+'@'+DB_CONF['host']+'/'+DB_CONF['database'] 
SQLALCHEMY_DATABASE_URI=conn_string

CONSUL_HOST = os.environ.get('CONSUL_URL', 'consul.example.com')
CONSUL_PORT = os.environ.get('CONSUL_PORT', 8301)

CONSUL_SCRAPE_INTERVAL = os.environ.get('CONSUL_SCRAPE_INTERVAL', 30) 

OAUTH_APP_NAME = os.environ.get('OAUTH_APP_NAME', 'consul-switcher')
GITLAB_HOST = os.environ.get('GITLAB_HOST', 'https://gitlab.com') 
GITLAB_CLIENT_ID = os.environ.get('GITLAB_CLIENT_ID', '')
GITLAB_CLIENT_SECRET = os.environ.get('GITLAB_CLIENT_SECRET', '')
