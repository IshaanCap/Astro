from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///astrology.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ==================== Database Models ====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    birth_time = db.Column(db.String(10), nullable=True)
    birth_place = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Horoscope(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sign = db.Column(db.String(20), nullable=False)
    prediction_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== Astrology Logic ====================

class AstrologyCalculator:
    ZODIAC_SIGNS = [
        ('Capricorn', '♑', 'Dec 22 - Jan 19'),
        ('Aquarius', '♒', 'Jan 20 - Feb 18'),
        ('Pisces', '♓', 'Feb 19 - Mar 20'),
        ('Aries', '♈', 'Mar 21 - Apr 19'),
        ('Taurus', '♉', 'Apr 20 - May 20'),
        ('Gemini', '♊', 'May 21 - Jun 20'),
        ('Cancer', '♋', 'Jun 21 - Jul 22'),
        ('Leo', '♌', 'Jul 23 - Aug 22'),
        ('Virgo', '♍', 'Aug 23 - Sep 22'),
        ('Libra', '♎', 'Sep 23 - Oct 22'),
        ('Scorpio', '♏', 'Oct 23 - Nov 21'),
        ('Sagittarius', '♐', 'Nov 22 - Dec 21')
    ]
    
    @staticmethod
    def get_zodiac_sign(date):
        month, day = date.month, date.day
        signs = [
            (1, 20, 'Capricorn'), (2, 19, 'Aquarius'), (3, 20, 'Pisces'),
            (4, 20, 'Aries'), (5, 21, 'Taurus'), (6, 21, 'Gemini'),
            (7, 23, 'Cancer'), (8, 23, 'Leo'), (9, 23, 'Virgo'),
            (10, 23, 'Libra'), (11, 22, 'Scorpio'), (12, 22, 'Sagittarius'),
            (12, 32, 'Capricorn')
        ]
        for end_month, end_day, sign in signs:
            if month == end_month and day <= end_day:
                return sign
            elif month < end_month:
                return sign
        return 'Capricorn'
    
    @staticmethod
    def get_sign_dates(sign):
        for name, symbol, dates in AstrologyCalculator.ZODIAC_SIGNS:
            if name.lower() == sign.lower():
                return dates
        return ""

class HoroscopeGenerator:
    SIGN_TRAITS = {
        'aries': ['Bold', 'Ambitious', 'Energetic', 'Confident', 'Impatient'],
        'taurus': ['Reliable', 'Patient', 'Practical', 'Devoted', 'Stubborn'],
        'gemini': ['Adaptable', 'Curious', 'Communicative', 'Witty', 'Nervous'],
        'cancer': ['Intuitive', 'Emotional', 'Protective', 'Creative', 'Moody'],
        'leo': ['Creative', 'Playful', 'Warm', 'Generous', 'Arrogant'],
        'virgo': ['Analytical', 'Practical', 'Loyal', 'Helpful', 'Critical'],
        'libra': ['Diplomatic', 'Fair-minded', 'Social', 'Romantic', 'Indecisive'],
        'scorpio': ['Passionate', 'Resourceful', 'Brave', 'Loyal', 'Jealous'],
        'sagittarius': ['Optimistic', 'Adventurous', 'Honest', 'Freedom-loving', 'Careless'],
        'capricorn': ['Disciplined', 'Responsible', 'Ambitious', 'Pessimistic', 'Bossy'],
        'aquarius': ['Progressive', 'Original', 'Independent', 'Humanitarian', 'Stubborn'],
        'pisces': ['Compassionate', 'Artistic', 'Intuitive', 'Gentle', 'Escapist']
    }
    
    @staticmethod
    def generate_daily_horoscope(sign):
        sign_lower = sign.lower()
        traits = HoroscopeGenerator.SIGN_TRAITS.get(sign_lower, ['Mysterious'])
        
        return {
            'sign': sign,
            'date': datetime.now().strftime('%B %d, %Y'),
            'traits': traits,
            'love': "Your stars align for romance today!",
            'career': "Your hard work pays off today!",
            'health': "Your energy levels are high!",
            'overall': f"Today brings exciting opportunities for {sign_lower}s. " +
                      f"Your natural {traits[0].lower()} nature helps you navigate challenges."
        }

# ==================== Routes ====================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/birth-chart', methods=['GET', 'POST'])
@login_required
def birth_chart():
    if request.method == 'POST':
        birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d')
        birth_time = request.form.get('birth_time')
        birth_place = request.form.get('birth_place')
        
        # Update user profile
        current_user.birth_date = birth_date
        current_user.birth_time = birth_time
        current_user.birth_place = birth_place
        db.session.commit()
        
        # Calculate zodiac sign
        sign = AstrologyCalculator.get_zodiac_sign(birth_date)
        dates = AstrologyCalculator.get_sign_dates(sign)
        
        return render_template('chart_result.html', sign=sign, dates=dates, 
                             birth_date=birth_date, birth_time=birth_time, 
                             birth_place=birth_place)
    
    return render_template('birth_chart.html')

@app.route('/horoscope')
@login_required
def horoscope():
    if not current_user.birth_date:
        flash('Please set your birth date first!', 'warning')
        return redirect(url_for('birth_chart'))
    
    sign = AstrologyCalculator.get_zodiac_sign(current_user.birth_date)
    horoscope_data = HoroscopeGenerator.generate_daily_horoscope(sign)
    
    return render_template('horoscope.html', horoscope=horoscope_data, sign=sign)

@app.route('/compatibility', methods=['GET', 'POST'])
@login_required
def compatibility():
    if request.method == 'POST':
        sign1 = request.form.get('sign1')
        sign2 = request.form.get('sign2')
        
        # Simple compatibility calculation
        score = 70 + hash(sign1 + sign2) % 30
        
        return render_template('compatibility_result.html', 
                             sign1=sign1, sign2=sign2, score=score)
    
    signs = [s[0] for s in AstrologyCalculator.ZODIAC_SIGNS]
    return render_template('compatibility.html', signs=signs)

@app.route('/api/zodiac-sign')
def api_zodiac_sign():
    date_str = request.args.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        sign = AstrologyCalculator.get_zodiac_sign(date)
        return {'sign': sign}
    return {'error': 'Date required'}, 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)