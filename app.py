from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'qslsecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# -------- MODELLER --------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    callsign = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class QSL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_callsign = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    band = db.Column(db.String(10))
    mode = db.Column(db.String(10))
    rst_sent = db.Column(db.String(10))
    rst_recv = db.Column(db.String(10))
    note = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------- ROTALAR --------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        callsign = request.form['callsign'].upper()
        password = request.form['password']
        if User.query.filter_by(callsign=callsign).first():
            flash('Bu çağrı işareti zaten kayıtlı.')
            return redirect(url_for('register'))
        new_user = User(callsign=callsign, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        callsign = request.form['callsign'].upper()
        password = request.form['password']
        user = User.query.filter_by(callsign=callsign, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Giriş başarısız.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        qsl = QSL(
            sender_id=current_user.id,
            receiver_callsign=request.form['to'].upper(),
            date=request.form['date'],
            time=request.form['time'],
            band=request.form['band'],
            mode=request.form['mode'],
            rst_sent=request.form['rst_sent'],
            rst_recv=request.form['rst_recv'],
            note=request.form['note']
        )
        db.session.add(qsl)
        db.session.commit()
        flash('QSL gönderildi!')
    sent_qsls = QSL.query.filter_by(sender_id=current_user.id).all()
    received_qsls = QSL.query.filter_by(receiver_callsign=current_user.callsign).all()
    for qsl in received_qsls:
        sender = User.query.get(qsl.sender_id)
        qsl.sender_callsign = sender.callsign if sender else "?"
    return render_template('dashboard.html', sent=sent_qsls, received=received_qsls)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

received_qsls = QSL.query.filter_by(receiver_callsign=current_user.callsign).all()
for qsl in received_qsls:
    sender = User.query.get(qsl.sender_id)
    qsl.sender_callsign = sender.callsign if sender else "?"
