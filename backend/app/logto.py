from authlib.integrations.flask_client import OAuth


oauth = OAuth()

def init_logto(app):
    oauth.init_app(app)
    #регистрация oauth как oath2-провайдера 
    oauth.register(
        name='authgear',
        client_id = app.config['AUTHGEAR_CLIENT_ID'],
        client_secret = app.config['AUTHGEAR_CLIENT_SECRET'],
        server_metadata_url = f"{app.config['AUTHGEAR_ISSUER']}/.well-known/openid-configuration", #endpoint с OIDC
        client_kwargs = {
            'scope': 'openid email profile',
            'client_auth_method': 'client_secret_basic',
        }
    )