from flask_oauthlib.client import OAuth

def get_google( app ):
    app.config['GOOGLE_ID'] =  '580557226207-ukigt720g3834henmlj546ucld47elnk.apps.googleusercontent.com' 
    app.config['GOOGLE_SECRET'] = 'G4QqN3B6Skock2eNiJfEk527'
    oauth = OAuth(app)
    google = oauth.remote_app(
        'google',
        consumer_key=app.config.get('GOOGLE_ID'),
        consumer_secret=app.config.get('GOOGLE_SECRET'),
        request_token_params={
            'scope': ['profile', 'https://www.googleapis.com/auth/userinfo.email']
            
        },
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )
    return google


