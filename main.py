
from flask import Flask, render_template, redirect, url_for, session, request, flash
import requests
import os
from urllib.parse import urlencode
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Discord OAuth2 configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', 'your_discord_client_id')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', 'your_discord_client_secret')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'https://your-repl-url.replit.dev/callback')

# In-memory storage for applied users (use database in production)
applied_users = set()

@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/login')
def login():
    # Generate Discord OAuth URL
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify email'
    }
    
    oauth_url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
    return redirect(oauth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    if not code:
        flash('Authorization failed')
        return redirect(url_for('index'))
    
    # Exchange code for access token
    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    token_response = requests.post('https://discord.com/api/oauth2/token', data=token_data, headers=headers)
    
    if token_response.status_code != 200:
        flash('Failed to get access token')
        return redirect(url_for('index'))
    
    token_json = token_response.json()
    access_token = token_json['access_token']
    
    # Get user info
    user_headers = {
        'Authorization': f"Bearer {access_token}"
    }
    
    user_response = requests.get('https://discord.com/api/users/@me', headers=user_headers)
    
    if user_response.status_code == 200:
        user_data = user_response.json()
        session['user'] = {
            'id': user_data['id'],
            'username': user_data['username'],
            'avatar': user_data.get('avatar'),
            'email': user_data.get('email')
        }
        flash('تم تسجيل الدخول بنجاح!')
    else:
        flash('Failed to get user info')
    
    return redirect(url_for('index'))

@app.route('/apply')
def apply():
    if 'user' not in session:
        flash('يجب تسجيل الدخول أولاً')
        return redirect(url_for('index'))
    
    user_id = session['user']['id']
    if user_id in applied_users:
        flash('لقد قمت بالتقديم بالفعل')
        return redirect(url_for('index'))
    
    return render_template('application.html', user=session['user'])

@app.route('/submit_application', methods=['POST'])
def submit_application():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user']['id']
    if user_id in applied_users:
        flash('لقد قمت بالتقديم بالفعل')
        return redirect(url_for('index'))
    
    # Add user to applied users
    applied_users.add(user_id)
    flash('تم إرسال طلبك بنجاح!')
    
    return redirect(url_for('index'))

@app.route('/ownership', methods=['GET', 'POST'])
def ownership():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'oswarden' and password == 'shallnotpass':
            session['owner'] = True
            return render_template('ownership_panel.html', applied_users=applied_users)
        else:
            flash('بيانات دخول خاطئة')
    
    return render_template('ownership_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
