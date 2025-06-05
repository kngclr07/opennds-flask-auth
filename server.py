from flask import Flask, request, render_template_string, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone

import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vouchers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(7), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def is_valid(self):
        now = datetime.now(timezone.utc)
        if not self.used:
            # Not used yet — valid indefinitely
            return True
        else:
            # Used — valid only if not expired
            if not self.expires_at:
                return False  # Defensive fallback
            if self.expires_at.tzinfo is None:
                self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
            return now < self.expires_at



with app.app_context():
    db.create_all()

def generate_voucher_code():
    return ''.join(random.choices('0123456789', k=7))

@app.route('/generate/<int:n>')
def generate(n):
    if n < 1 or n > 1000:
        return "Please request between 1 and 1000 vouchers.", 400

    codes = []
    for _ in range(n):
        while True:
            code = generate_voucher_code()
            if not Voucher.query.filter_by(code=code).first():
                break
        v = Voucher(code=code)
        db.session.add(v)
        codes.append(code)
    db.session.commit()

    # HTML template for displaying codes
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Voucher Codes</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
                padding: 20px;
            }
            .grid-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }
            .card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 10px;
                text-align: center;
            }
            .code {
                font-size: 1.5em;
                color: #333;
                margin-bottom: 5px;
            }
            .details {
                font-size: 0.9em;
                color: #555;
            }
        </style>
    </head>
    <body>
        <h1>Generated Voucher Codes</h1>
        <div class="grid-container">
            {% for code in codes %}
            <div class="card">
                <div class="code">Code: {{ code }}</div>
                <div class="details">Duration: 24:00:00</div>
                <div class="details">Data volume: Unlimited</div>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    '''

    # Render the HTML with the generated codes
    rendered_html = render_template_string(html_template, codes=codes)

    # Save to a file (e.g., vouchers.html)
    with open('vouchers.html', 'w') as f:
        f.write(rendered_html)

    return f"Successfully generated {n} vouchers and saved to vouchers.html."
LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>WiFiVault</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      height: 100vh;
      font-family: 'Inter', Arial, sans-serif;
      background: linear-gradient(135deg, #6a11cb, #2575fc);
      display: flex;
      justify-content: center;
      align-items: center;
      color: #333;
    }

    .login-container {
      background: #fff;
      padding: 40px 35px;
      border-radius: 12px;
      box-shadow: 0 12px 30px rgba(38, 44, 76, 0.15);
      width: 320px;
      text-align: center;
      transition: transform 0.3s ease;
    }
    .login-container:hover {
      transform: translateY(-5px);
      box-shadow: 0 20px 40px rgba(38, 44, 76, 0.25);
    }

    h2 {
      margin-bottom: 28px;
      font-weight: 600;
      font-size: 1.5rem;
      color: #1a1a1a;
      letter-spacing: 0.05em;
    }

    form {
      display: flex;
      flex-direction: column;
    }

    .input-wrapper {
      position: relative;
      margin-bottom: 20px;
    }

    input[type="text"] {
      width: 100%;
      padding: 12px 15px 12px 42px;
      border: 2px solid #ddd;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 400;
      transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }

    input[type="text"]:focus {
      outline: none;
      border-color: #2575fc;
      box-shadow: 0 0 8px rgba(37, 117, 252, 0.5);
    }

    /* Icon inside input */
    .input-wrapper::before {
      content: '\\1F511'; /* Unicode lock emoji */
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 18px;
      color: #999;
      pointer-events: none;
      user-select: none;
    }

    button {
      padding: 12px 0;
      background: #2575fc;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      font-size: 16px;
      color: white;
      cursor: pointer;
      transition: background-color 0.3s ease, box-shadow 0.3s ease;
      box-shadow: 0 6px 15px rgba(37, 117, 252, 0.4);
    }

    button:hover {
      background-color: #1a52c0;
      box-shadow: 0 8px 20px rgba(26, 82, 192, 0.6);
    }

    p.error {
      margin-top: 20px;
      color: #e03e3e;
      font-weight: 600;
      font-size: 0.9rem;
      user-select: none;
      letter-spacing: 0.02em;
    }
  </style>
</head>
<body>
  <div class="login-container">
    <h2>WIFI</h2>
    <form method="POST" autocomplete="off" novalidate>
      <div class="input-wrapper">
        <input type="text" name="code" maxlength="7" pattern="\\d{7}" placeholder="7-digit voucher code" required autofocus>
      </div>
      <button type="submit">Connect</button>
    </form>
    {% if message %}
      <p class="error">{{ message }}</p>
    {% endif %}
  </div>
</body>
</html>
'''

class UserAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ip = db.Column(db.String(45), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_active(self):
        if self.expires_at.tzinfo is None:
        # Assume it's in UTC and make it timezone-aware
           self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < self.expires_at

with app.app_context():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = "Hello"
    client_ip = request.args.get('clientip') or request.remote_addr
    gateway_name = request.args.get('gatewayname', 'WiFi Gateway')
    token = request.args.get('token')
    redir = request.args.get('redir') or 'http://google.com'
    auth_domain = request.args.get('auth_domain', '')
    auth_dir = request.args.get('auth_dir', '')
    origin_url = request.args.get('originurl', '')

    access = UserAccess.query.filter_by(user_ip=client_ip).first()
    if access and access.is_active():
        # User already has active access → authorize immediately
        return Response("Auth: 1\n", mimetype='text/plain')

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if not code or len(code) != 7 or not code.isdigit():
            message = 'Please enter a valid 7-digit code'
        else:
            voucher = Voucher.query.filter_by(code=code).first()
            if not voucher:
                message = 'Invalid voucher code'
            else:
                # Valid voucher: grant access and delete voucher
                db.session.delete(voucher)
                new_access = UserAccess(
                    user_ip=client_ip,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                db.session.add(new_access)
                db.session.commit()
                return Response("Auth: 1\n", mimetype='text/plain')

    # If GET or POST with errors, render login form with message
    return render_template('login.html', message=message, gateway_name=gateway_name, redir=redir)

@app.route('/status')
def status():
    return jsonify({'status': 'ok', 'time': datetime.now(timezone.utc).isoformat()})

@app.route('/auth', methods=['GET'])
def auth():
    client_ip = request.args.get('clientip')
    if not client_ip:
        return jsonify({'error': 'clientip parameter missing'}), 400

    access = UserAccess.query.filter_by(user_ip=client_ip).first()
    if access and access.is_active():
        return jsonify({
            'authenticated': True,
            'username': f"user_{client_ip}",
            'session_timeout': 86400,
            'download_quota': 0,
            'upload_quota': 0,
            'idle_timeout': 0
        })
    else:
        return jsonify({'authenticated': False})

@app.route('/logout', methods=['GET'])
def logout():
    client_ip = request.args.get('clientip')
    if client_ip:
        UserAccess.query.filter_by(user_ip=client_ip).delete()
        db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/admin/active_users')
def active_users():
    users = UserAccess.query.all()
    active_list = []
    now = datetime.now(timezone.utc)
    for u in users:
        if u.expires_at.tzinfo is None:
            u.expires_at = u.expires_at.replace(tzinfo=timezone.utc)
        active_list.append({
            'ip': u.user_ip,
            'expires_at': u.expires_at.isoformat(),
            'is_active': now < u.expires_at
        })
    return {'active_users': active_list}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
