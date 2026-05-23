# pip install flask flask_sqlalchemy flask_bcrypt flask_cors pyjwt

from flask import Flask, render_template, request
from flask import redirect, url_for, session, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from sqlalchemy import inspect, text
from werkzeug.utils import secure_filename

import jwt
import datetime
import os
import re

from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ANOTARA_SECRET_KEY'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anotara.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = os.path.join(
    app.root_path,
    'static',
    'uploads'
)

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

CORS(app)


@app.template_filter("tips_bullets")
def tips_bullets(tips):
    """Split travel tips into separate lines for bullet lists."""
    if tips is None:
        return []
    if isinstance(tips, (list, tuple)):
        return [str(t).strip() for t in tips if str(t).strip()]
    text = str(tips).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    contact_number = db.Column(
        db.String(20),
        nullable=False
    )

    profile_picture = db.Column(
        db.String(255),
        nullable=True
    )

    bookings = db.relationship(
        'Booking',
        backref='user',
        lazy=True
    )


class Booking(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tourist_spot = db.Column(
        db.String(200),
        nullable=False
    )

    booking_date = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow
    )

    desired_date = db.Column(
        db.Date,
        nullable=True
    )

    desired_time = db.Column(
        db.Time,
        nullable=True
    )

    accommodation_check_in = db.Column(
        db.Date,
        nullable=True
    )

    accommodation_check_in_time = db.Column(
        db.Time,
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default='pending'
    )


class Admin(db.Model):

    __tablename__ = 'admins'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    contact_number = db.Column(
        db.String(20),
        nullable=False
    )

with app.app_context():

    os.makedirs(
        app.config['UPLOAD_FOLDER'],
        exist_ok=True
    )

    db.create_all()

    inspector = inspect(db.engine)

    user_columns = [
        column['name']
        for column in inspector.get_columns('user')
    ]

    booking_columns = [
        column['name']
        for column in inspector.get_columns('booking')
    ]

    if 'profile_picture' not in user_columns:

        db.session.execute(
            text('ALTER TABLE user ADD COLUMN profile_picture VARCHAR(255)')
        )

    if 'desired_date' not in booking_columns:

        db.session.execute(
            text('ALTER TABLE booking ADD COLUMN desired_date DATE')
        )

    if 'desired_time' not in booking_columns:

        db.session.execute(
            text('ALTER TABLE booking ADD COLUMN desired_time TIME')
        )

    if 'accommodation_check_in' not in booking_columns:

        db.session.execute(
            text('ALTER TABLE booking ADD COLUMN accommodation_check_in DATE')
        )

    if 'accommodation_check_in_time' not in booking_columns:

        db.session.execute(
            text('ALTER TABLE booking ADD COLUMN accommodation_check_in_time TIME')
        )

    if 'status' not in booking_columns:

        db.session.execute(
            text(
                "ALTER TABLE booking ADD COLUMN status VARCHAR(20) "
                "NOT NULL DEFAULT 'pending'"
            )
        )

    db.session.commit()

tourist_spots = [

    {
        "id": 1,
        "name": "Britania Islands",
        "location": "San Agustin, Surigao del Sur",
        "description": "It is famous for its powdery white sandbars, crystal-clear turquoise waters, and peaceful tropical scenery.",
        "tips": "Visit during summer or dry season (March–May) for calmer seas and clearer water."
                "Bring cash, since ATMs and card payments are limited in the area." 
                "Wear sunscreen, hats, slippers, and bring extra clothes because island hopping can get very sunny."
                "Start island hopping early in the morning for better weather and fewer crowds."
                "Bring waterproof bags to protect gadgets and valuables."
                "Practice responsible tourism by avoiding littering and respecting marine life.",
        "image": "/static/images/britania.jpg"
    },

    {
        "id": 2,
        "name": "Hinatuan Enchanted River",
        "location": "Hinatuan, Surigao del Sur",
        "description": "It is known for its crystal-clear deep blue water that changes shades from turquoise to sapphire.",
        "tips": "Visit early in the morning to avoid crowds and enjoy clearer photos."
                "Best time to visit is during the dry season from March to May."
                "Bring cash because digital payments and ATMs are limited in the area."
                "Wear aqua shoes or slippers with good grip since pathways can get slippery."
                "Bring waterproof bags for gadgets and valuables."
                "Mobile signal can become weak in some areas, so download maps beforehand.",
        "image": "/static/images/enchanted.jpg"

    },

    {
        "id": 3,
        "name": "Tinuy-an Falls",
        "location": "Bislig, Surigao del Sur",
        "description": "Often called the “Little Niagara Falls of the Philippines” because of its wide curtain-like cascades.",
        "tips": "Visit early in the morning for cooler weather, fewer visitors, and the famous rainbow view."
                "Wear slippers or aqua shoes with good grip because rocks and pathways can become slippery."
                "Bring extra clothes, waterproof bags, and towels if you plan to swim or ride the bamboo raft."
                "The road going to the falls can be rough in some areas, so prepare for a long habal-habal or vehicle ride from Bislig City."
                "Bring cash since some nearby stores and cottages may not accept digital payments."
                "Respect the environment by avoiding littering and following local tourism rules.",
        "image": "/static/images/tinuyan.jpg"
    },

    {
        "id": 4,
        "name": "Libuacan Cold Spring",
        "location": "Tagbina, Surigao del Sur",
        "description": "A refreshing cold spring river surrounded by trees and nature, perfect for swimming and relaxation.",
        "tips": "Visit early in the morning for a quieter and more peaceful experience."
                "Bring extra clothes, towels, and waterproof bags if you plan to swim."
                "Wear slippers or aqua shoes because some areas can be slippery."
                "Bring your own food and drinks since dining options nearby are limited."
                "Practice proper waste disposal and avoid using soap or shampoo in the spring to help preserve the clean water."
                "Mobile signal may be weak in some areas, so download maps or contact information beforehand.",
        "image": "/static/images/libuacan.jpg"
    },

    {
        "id": 5,
        "name": "Bao-Bao Falls",
        "location": "San Miguel, Surigao del Sur",
        "description": "a natural waterfall attraction associated with Surigao del Sur, known for its clear freshwater, rocky cascades, and refreshing swimming pools.",
        "tips": "Visit early in the morning for fewer crowds and cooler weather."
                "Wear non-slip sandals or aqua shoes because rocks and pathways can get slippery."
                "Bring extra clothes and towels since changing rooms are limited."
                "Mobile signal may be weak in some areas, so inform companions beforehand."
                "Practice CLAYGO (Clean As You Go) to help preserve the falls."
                "Be careful near deeper sections if you are not a strong swimmer.",
        "image": "/static/images/baobao.jpg"
    },

    {
        "id": 6,
        "name": "Cagwait White Beach",
        "location": "Cagwait, Surigao del Sur",
        "description": "Known as the “Boracay of Caraga,” Cagwait White Beach is famous for its long crescent-shaped shoreline, powdery white sand, and relaxing turquoise waters.",
        "tips": "Visit during summer (March–May) for calm waters and clearer skies."
                "Go early morning or late afternoon for cooler weather and better photos."
                "Bring sunscreen, umbrella, and extra drinking water since shade can be limited on some parts of the beach."
                "Expect stronger waves during rainy or windy days because the beach faces the Pacific Ocean."
                "Wear slippers or sandals comfortable for walking on long stretches of sand."
                "Keep the beach clean and avoid leaving plastic waste behind.",
        "image": "/static/images/cagwait.jpg"
    },

    {
        "id": 7,
        "name": "International Doll House",
        "location": "Bislig City, Surigao del Sur",
        "description": "A unique museum featuring rare and expensive dolls from around the world.",
        "tips": "Visit during daytime for better views and cooler travel conditions."
                "Prepare for a stair climb of more than 200 steps going to the attraction."
                "Wear comfortable footwear because the pathway and stairs can be tiring."
                "Ask ahead about opening schedules since some visitors reported limited operating days during certain seasons."
                "Avoid touching the dolls because many are delicate and expensive collectibles."
                "Bring a camera since the place has scenic overlooking views of Bislig City and the sea.",
        "image": "/static/images/dollhouse.jpg"
    },

    {
        "id": 8,
        "name": "Harip Beach",
        "location": "Barobo, Surigao del Sur",
        "description": "A peaceful beach with fine sand and calm waters ideal for relaxation.",
        "tips": "Visit during sunny weather for clearer water and better beach views."
                "Bring your own food and drinking water because nearby stores may be limited during weekdays."
                "Wear slippers or aqua shoes since some areas have small rocks and shells."
                "Bring a tent or reserve a cottage early if visiting during weekends or holidays."
                "Stay hydrated and use sunscreen because the beach can get very hot at noon."
                "Keep valuables safe and avoid leaving trash on the beach.",
        "image": "/static/images/harip.jpg"
    },

    {
        "id": 9,
        "name": "Malinawa Cool Spring",
        "location": "Cantilan, Surigao del Sur",
        "description": "a refreshing natural spring known for its crystal-clear, ice-cold freshwater that flows from underground sources.",
        "tips": "Visit in the morning for colder water and fewer visitors."
                "Bring extra clothes, towels, and waterproof bags for gadgets."
                "Wear non-slip slippers because pathways near the spring may be wet and slippery."
                "Weekends and holidays can get crowded, so arrive early if you want a good cottage spot."
                "Respect the cleanliness of the spring by avoiding plastic litter and food waste."
                "Be cautious when swimming in deeper portions, especially with children.",
        "image": "/static/images/malinawa.jpg"
    },

    {
        "id": 10,
        "name": "Hinayagan Cave",
        "location": "Barobo, Surigao del Sur",
        "description": "A fascinating natural cave system known for its wide opening, dramatic rock formations, and a beautiful underground lagoon with clear blue-green water.",
        "tips": "Hire a local guide before entering the cave for safety and easier navigation."
                "Wear comfortable clothes and non-slip footwear because cave floors can be wet and slippery."
                "Bring a flashlight or headlamp since some cave sections are dark."
                "Avoid touching stalactites and stalagmites to help preserve the cave formations."
                "Visit during good weather because heavy rain may make cave trails muddy or unsafe."
                "Travel with companions instead of exploring alone.",
        "image": "/static/images/hinayagan.jpg"
    },

    {
        "id": 11,
        "name": "Sian Falls",
        "location": "Lingig, Surigao del Sur",
        "description": "A refreshing multi-level waterfall known for its clear blue-green water, natural rock pools, and lush forest surroundings",
        "tips": "Visit during summer or sunny days for safer trails and clearer water."
                "Wear non-slip sandals or aqua shoes because rocks near the falls can be slippery."
                "Bring food and drinking water since stores near the area may be limited."
                "Travel early in the morning to avoid crowds and enjoy cooler weather."
                "Keep gadgets protected using waterproof bags or phone cases."
                "Respect the environment by avoiding littering and loud noise.",
        "image": "/static/images/sian.jpg"
    },

    {
        "id": 12,
        "name": "Hagonoy Island Beach",
        "location": "San Agustin, Surigao del Sur",
        "description": "It is known for its powdery white sand, clear turquoise water, coconut trees, and peaceful tropical atmosphere.",
        "tips": "Visit early in the morning for calmer seas, cooler weather, and fewer tourists."
                "Best time to visit is during the dry season from March to May."
                "Bring sunscreen, hats, sunglasses, and drinking water because shaded areas can be limited."
                "Wear aqua shoes or slippers for comfortable walking on rocky and sandy areas."
                "Bring waterproof bags to protect gadgets during island hopping."
                "Mobile signal may become weak while on the islands, so inform companions beforehand."
                "Practice responsible tourism by avoiding littering and protecting marine life.",
        "image": "/static/images/hagonoy.jpg"
    },

    {
        "id": 13,
        "name": "Mendezona Falls",
        "location": "Tago, Surigao del Sur",
        "description": "It is known for its cool flowing water, peaceful forest surroundings, and refreshing atmosphere that makes it perfect for nature lovers and adventure seekers.",
        "tips": "Visit during the morning for cooler weather and a more peaceful experience."
                "Wear comfortable clothes, aqua shoes, or slippers with good grip because trails and rocks may be slippery."
                "Bring drinking water, snacks, and extra clothes if you plan to swim."
                "Waterproof bags are helpful for protecting gadgets and valuables."
                "Mobile signal may be weak in some parts of the area, so inform companions before traveling."
                "Avoid visiting during heavy rains because trails can become muddy and water currents may become stronger."
                "Practice responsible tourism by keeping the area clean and avoiding damage to nature.",
        "image": "/static/images/mendezona.jpg"
    },

    {
        "id": 14,
        "name": "Lawigan Beach",
        "location": "Barobo, Surigao del Sur",
        "description": "Is a peaceful coastal destination known for its long shoreline, clear waters, fresh sea breeze, and relaxing atmosphere.",
        "tips": "Visit early in the morning or late afternoon to avoid intense heat and enjoy the best beach views."
                "Bring sunscreen, hats, sunglasses, and enough drinking water."
                "Wear comfortable beach slippers or aqua shoes, especially when exploring rocky parts of the shore."
                "Bring extra clothes, towels, and waterproof bags if you plan to swim."
                "Mobile signal may vary depending on the exact location, so download maps beforehand if needed."
                "Keep the beach clean by properly disposing of trash and avoiding damage to marine life."
                "Check weather conditions before traveling, especially during rainy season or rough sea conditions.",
        "image": "/static/images/lawigan.jpg"
    },

    {
        "id": 15,
        "name": "Laswitan Falls and Lagoon",
        "location": "Cortes, Surigao del Sur",
        "description": "A unique natural attraction famous for its “wave-like waterfall” effect. Instead of a tall vertical waterfall, seawater rushes over layered rock formations during high tide, creating a dramatic cascading effect that looks similar to a mini Niagara Falls.",
        "tips": "Visit during high tide to witness the famous cascading “waterfall” effect."
                "Wear aqua shoes or slippers with good grip because rocks can be sharp and slippery."
                "Bring sunscreen, hats, towels, and extra clothes if you plan to swim."
                "Waterproof bags are recommended to protect gadgets from splashes and seawater."
                "Avoid standing too close to strong waves during rough sea conditions for safety."
                "Bring drinking water and snacks because food stalls may be limited depending on the season."
                "Keep the area clean and avoid leaving trash on the rocks or lagoon area.",
        "image": "/static/images/laswitan.jpg"
    },

    {
    "id": 16,
    "name": "Magkawas Falls",
    "location": "Sibahay, Lanuza, Surigao del Sur",
    "description": "A beautiful hidden waterfall destination surrounded by lush greenery and natural rock formations. It is known for its cool, crystal-clear water and peaceful environment, making it a perfect place for relaxation, swimming, and nature trips.",
    "tips": "Visit during the morning for cooler weather and a more relaxing experience."
            "Wear comfortable outdoor clothing and aqua shoes or slippers with good grip because trails and rocks may be slippery."
            "Bring extra clothes, towels, and waterproof bags if you plan to swim."
            "Prepare snacks and drinking water since stores near the falls may be limited."
            "Avoid visiting during heavy rain because trails can become muddy and water currents may become stronger."
            "Keep the surroundings clean and avoid damaging plants or natural rock formations."
            "Mobile signal may be weak in some parts of the area, so inform companions beforehand.",
    "image": "/static/images/magkawas.jpg"
    },

    {
    "id": 17,
    "name": "Silop Cool Spring",
    "location": "Agsam, Lanuza, Surigao del Sur",
    "description": "A serene, natural cold spring destination known for its crystal-clear water and lush surroundings. It is a popular, affordable spot for swimming and relaxation, often visited after exploring the nearby Campamento Caves.",
    "tips": "Visit early in the morning or late afternoon for cooler weather and a more peaceful experience."
            "Wear comfortable clothes and aqua shoes or slippers because some areas may be slippery."
            "Bring extra clothes, towels, and waterproof bags if you plan to swim."
            "Prepare drinking water and snacks since nearby food stalls may be limited."
            "Avoid visiting during heavy rain because pathways may become muddy and slippery."
            "Keep the spring clean by properly disposing of trash and avoiding harmful chemicals in the water."
            "Mobile signal may be weak in some areas, so inform companions before your trip.",
    "image": "/static/images/silop.jpg"
    },

    {
    "id": 18,
    "name": "Sanctuary Cafe",
    "location": "Sibahay, Lanuza, Surigao del Sur",
    "description": "A relaxing seaside stop located near the Lanuza Marine Park and Sanctuary. The café is known for its peaceful coastal atmosphere, ocean views, cool sea breeze, and natural surroundings.",
    "tips": "Visit during the morning or late afternoon for cooler weather and better seaside views."
            "Bring sunscreen, hats, and drinking water since the coastal area can become hot during midday."
            "Wear comfortable footwear because some viewing areas and rocky sections may be slippery."
            "Bring cameras or phones for scenic ocean and coastal photography."
            "Respect marine conservation rules and avoid throwing trash into the sea or sanctuary areas."
            "Mobile signal may vary depending on the exact coastal location."
            "Bring cash because digital payments may not always be available in smaller establishments nearby.",
    "image": "/static/images/sanctuary.jpg"
    },

    {
    "id": 19,
    "name": "Hubason River",
    "location": "Carmen, Surigao del Sur",
    "description": "A peaceful freshwater river spot known for its clear water, natural rock formations, and relaxing swimming areas. It’s not heavily commercialized, so it offers a more “local and natural” experience compared to popular tourist destinations.",
    "tips": "Visit early in the morning for cooler weather and fewer visitors."
            "Wear aqua shoes or slippers with good grip because river rocks can be slippery."
            "Bring extra clothes, towels, and a waterproof bag for your belongings."
            "Prepare snacks and drinking water since nearby stores may be limited."
            "Always check water conditions before swimming, especially after heavy rain."
            "Be careful in deeper sections of the river and avoid diving in unfamiliar areas."
            "Keep the area clean—bring your trash with you to help preserve the natural spot.",
    "image": "/static/images/hubason.jpg"
    },

    {
    "id": 20,
    "name": "Sua Cool Spring",
    "location": "Esperanza, Carmen, Surigao del Sur",
    "description": "A refreshing natural spring known for its crystal-clear, ice-cold water sourced from underground streams. It features natural pools surrounded by trees and greenery, giving it a calm and relaxing “hidden gem” vibe that locals often visit for swimming and family bonding.",
    "tips": "Visit early morning or late afternoon for a more peaceful experience and cooler weather."
            "Wear aqua shoes or slippers with good grip since rocks and pathways can be slippery."
            "Bring extra clothes, towels, and waterproof bags for your belongings."
            "Prepare snacks and drinking water because nearby food options may be limited."
            "Avoid using soaps or shampoos in the spring to help protect its clean water."
            "Be careful in deeper areas and always check water depth before swimming."
            "Bring cash since small springs like this usually don’t accept digital payments.",
    "image": "/static/images/sua.jpg"
    },

    {
    "id": 21,
    "name": "Surf Camp",
    "location": "Lanuza, Surigao del Sur",
    "description": "one of the most well-known surfing destinations in Mindanao. It sits along the Pacific coastline, where consistent waves make it ideal for both beginners and experienced surfers.",
    "tips": "Best surfing season is usually during the Amihan (northeast monsoon) months from October to March when waves are stronger and more consistent."
            "Beginners should hire a local instructor for safety and proper surfing basics."
            "Wear rash guards, reef-safe sunscreen, and comfortable swimwear to protect from sun and board friction."
            "Bring waterproof bags for gadgets and valuables."
            "Be careful of strong currents and always follow local safety instructions."
            "Early morning sessions are best for calmer winds and better wave conditions."
            "Bring cash since surf camps and small shops may not always accept online payments.",
    "image": "/static/images/surfcamp.jpg"
    },

    {
    "id": 22,
    "name": "Kilometro 5",
    "location": "Agsam, Lanuza, Surigao del Sur",
    "description": "It is a popular, affordable nature destination offering panoramic views of Lanuza Bay and the mountains, with attractions including glamping, a view deck, and proximity to inland adventures.",
    "tips": "Visit early morning or late afternoon for the best lighting and cooler weather."
            "Be careful when stopping along the roadside—park safely away from traffic."
            "Bring water, snacks, and sun protection since there are no major stores nearby."
            "Wear comfortable footwear if you plan to explore nearby rocky areas."
            "Keep your gadgets secure when taking photos near cliffs."
            "Mobile signal may be weak depending on exact location.",
    "image": "/static/images/kilometro5.jpg"
    },

    {
    "id": 23,
    "name": "Aceyoung Paradise",
    "location": "Sibahay, Lanuza, Surigao del Sur",
    "description": "It is known for its panoramic 360-degree views of the Lanuza coastline and lush landscapes, featuring amenities like air-conditioned rooms, a viewing deck, and a laid-back, rustic atmosphere.",
    "tips": "Visit early morning or late afternoon for cooler weather and the best ocean views."
            "Bring sunscreen, hats, and drinking water to stay protected from the sun."
            "Wear comfortable beachwear and slippers or aqua shoes for easier movement near the shore."
            "Pack extra clothes and waterproof bags if you plan to swim or stay overnight."
            "Always check sea conditions before swimming, as waves can be strong in some seasons."
            "Bring cash since small resorts may have limited or no digital payment options."
            "Respect quiet hours and keep the area clean to preserve its peaceful environment.",
    "image": "/static/images/aceyoung.jpg"
    },

    {
    "id": 24,
    "name": "Floating Kingdom",
    "location": "Nurcia, Lanuza, Surigao del Sur",
    "description": "It features beach view villas, a swimming pool, a skateboard practice area, and a cafe, offering a tropical escape with ocean views, a bonfire area, and live acoustic",
    "tips": "Visit early morning or late afternoon for cooler weather and a more peaceful atmosphere."
            "Wear light, comfortable clothing and slippers or aqua shoes for easy movement on floating platforms."
            "Bring sunscreen, hats, and drinking water, especially during sunny days."
            "Secure your gadgets in waterproof bags to avoid accidents near water."
            "Be careful when walking on floating cottages as they may move slightly with water currents."
            "Bring cash since small eco-tourism sites may not accept digital payments."
            "Respect the natural environment—avoid throwing trash into the river.",
    "image": "/static/images/floatingkingdom.jpg"
    }
]

def token_required(f):

    @wraps(f)

    def decorated(*args, **kwargs):

        token = None

        if 'Authorization' in request.headers:

            token = request.headers['Authorization']

        if not token:

            return jsonify({
                'message': 'Token Missing'
            }), 401

        try:

            data = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=["HS256"]
            )

            current_user = User.query.get(
                data['id']
            )

        except:

            return jsonify({
                'message': 'Invalid Token'
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/')
def welcome():

    return render_template(
        'welcome.html'
    )

@app.route('/login')
def login_page():

    error = request.args.get('error')

    return render_template(
        'login.html',
        error=error
    )

@app.route('/register')
def register_page():

    return render_template(
        'register.html'
    )

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    return render_template(
        'dashboard.html',
        tourist_spots=tourist_spots
    )

@app.route('/details/<int:spot_id>')
def details(spot_id):

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    user = User.query.get(
        session['user_id']
    )

    selected_spot = None

    for spot in tourist_spots:

        if spot['id'] == spot_id:

            selected_spot = spot

            break

    return render_template(
        'details.html',
        spot=selected_spot,
        user=user
    )

@app.route('/profile')
def profile():

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    user = User.query.get(
        session['user_id']
    )

    bookings = Booking.query.filter_by(
        user_id=user.id
    ).order_by(
        Booking.booking_date.desc()
    ).all()

    return render_template(
        'profile.html',
        user=user,
        bookings=bookings
    )

@app.route('/register-user', methods=['POST'])
def register_user():

    username = request.form['username']

    password = request.form['password']

    contact_number = request.form['contact_number']


    existing_user = User.query.filter_by(
        username=username
    ).first()

    if existing_user:

        return "Username already exists!"


    hashed_password = bcrypt.generate_password_hash(
        password
    ).decode('utf-8')


    new_user = User(
        username=username,
        password=hashed_password,
        contact_number=contact_number
    )

    db.session.add(new_user)

    db.session.commit()

    return redirect(
        url_for('login_page')
    )

@app.route('/login-user', methods=['POST'])
def login_user():

    username = request.form['username']

    password = request.form['password']

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:

        return redirect(
            url_for(
                'login_page',
                error='user_not_found'
            )
        )


    if bcrypt.check_password_hash(
        user.password,
        password
    ):


        session['user_id'] = user.id

        session.pop('admin_id', None)


        token = jwt.encode({

            'id': user.id,

            'exp':
            datetime.datetime.utcnow()
            + datetime.timedelta(hours=24)

        },
        app.config['SECRET_KEY'],
        algorithm="HS256")

        session['token'] = token

        return redirect(
            url_for('dashboard')
        )

    return redirect(
        url_for(
            'login_page',
            error='invalid_password'
        )
    )

@app.route('/book/<int:spot_id>', methods=['POST'])
def book(spot_id):

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    selected_spot = None

    for spot in tourist_spots:

        if spot['id'] == spot_id:

            selected_spot = spot

            break

    if not selected_spot:

        return "Tourist Spot Not Found"

    desired_date = None

    if request.form.get('desired_date'):

        desired_date = datetime.datetime.strptime(
            request.form['desired_date'],
            '%Y-%m-%d'
        ).date()

    desired_time = None

    if request.form.get('desired_time'):

        desired_time = datetime.datetime.strptime(
            request.form['desired_time'],
            '%H:%M'
        ).time()

    accommodation_check_in = None

    if request.form.get('accommodation_check_in'):

        accommodation_check_in = datetime.datetime.strptime(
            request.form['accommodation_check_in'],
            '%Y-%m-%d'
        ).date()

    accommodation_check_in_time = None

    if request.form.get('accommodation_check_in_time'):

        accommodation_check_in_time = datetime.datetime.strptime(
            request.form['accommodation_check_in_time'],
            '%H:%M'
        ).time()

    new_booking = Booking(

        tourist_spot=selected_spot['name'],

        desired_date=desired_date,

        desired_time=desired_time,

        accommodation_check_in=accommodation_check_in,

        accommodation_check_in_time=accommodation_check_in_time,

        user_id=session['user_id'],

        status='pending'
    )

    db.session.add(new_booking)

    db.session.commit()

    return redirect(
        url_for('profile')
    )

@app.route('/edit-booking/<int:booking_id>', methods=['POST'])
def edit_booking(booking_id):

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=session['user_id']
    ).first()

    if not booking:

        return "Booking Not Found"

    booking.desired_date = None

    if request.form.get('desired_date'):

        booking.desired_date = datetime.datetime.strptime(
            request.form['desired_date'],
            '%Y-%m-%d'
        ).date()

    booking.desired_time = None

    if request.form.get('desired_time'):

        booking.desired_time = datetime.datetime.strptime(
            request.form['desired_time'],
            '%H:%M'
        ).time()

    booking.accommodation_check_in = None

    if request.form.get('accommodation_check_in'):

        booking.accommodation_check_in = datetime.datetime.strptime(
            request.form['accommodation_check_in'],
            '%Y-%m-%d'
        ).date()

    booking.accommodation_check_in_time = None

    if request.form.get('accommodation_check_in_time'):

        booking.accommodation_check_in_time = datetime.datetime.strptime(
            request.form['accommodation_check_in_time'],
            '%H:%M'
        ).time()

    db.session.commit()

    return redirect(
        url_for('profile')
    )

@app.route('/delete-booking/<int:booking_id>', methods=['POST'])
def delete_booking(booking_id):

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=session['user_id']
    ).first()

    if not booking:

        return "Booking Not Found"

    db.session.delete(booking)

    db.session.commit()

    return redirect(
        url_for('profile')
    )

@app.route('/edit-profile', methods=['POST'])
def edit_profile():

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    user = User.query.get(
        session['user_id']
    )

    user.username = request.form['username']

    user.contact_number = request.form['contact_number']

    profile_picture = request.files.get('profile_picture')

    if profile_picture and profile_picture.filename:

        filename = secure_filename(
            profile_picture.filename
        )

        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:

            saved_filename = f"user_{user.id}_{filename}"

            profile_picture.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    saved_filename
                )
            )

            user.profile_picture = f"uploads/{saved_filename}"

    db.session.commit()

    return redirect(
        url_for('profile')
    )

@app.route('/admin-register')
def admin_register_page():

    return render_template(
        'admin_register.html'
    )

@app.route('/register-admin', methods=['POST'])
def register_admin():

    username = request.form['admin_username']

    password = request.form['admin_password']

    contact_number = request.form['admin_contact']

    existing = Admin.query.filter_by(
        username=username
    ).first()

    if existing:

        return "Admin username already exists!"

    hashed_password = bcrypt.generate_password_hash(
        password
    ).decode('utf-8')

    new_admin = Admin(
        username=username,
        password=hashed_password,
        contact_number=contact_number
    )

    db.session.add(new_admin)

    db.session.commit()

    return redirect(
        url_for('admin_login')
    )

@app.route('/admin-login')
def admin_login():

    return render_template(
        'admin_login.html'
    )

@app.route('/login-admin', methods=['POST'])
def login_admin():

    username = request.form['admin_username']

    password = request.form['admin_password']

    admin = Admin.query.filter_by(
        username=username
    ).first()

    if not admin:

        return "Admin account not found!"

    if bcrypt.check_password_hash(
        admin.password,
        password
    ):

        session['admin_id'] = admin.id

        session.pop('user_id', None)

        session.pop('token', None)

        return redirect(
            url_for('admin_dashboard')
        )

    return "Invalid password!"

@app.route('/delete-account', methods=['POST'])
def delete_account():

    if 'user_id' not in session:

        return redirect(
            url_for('welcome')
        )

    user = User.query.get(
        session['user_id']
    )


    Booking.query.filter_by(
        user_id=user.id
    ).delete()


    db.session.delete(user)

    db.session.commit()


    session.clear()

    return redirect(
        url_for('welcome')
    )

@app.route('/admin-dashboard')
def admin_dashboard():

    if 'admin_id' not in session:

        return redirect(
            url_for('admin_login')
        )

    return render_template(
        'admin_dashboard.html',
        users=User.query.all(),
        bookings=Booking.query.order_by(
            Booking.booking_date.desc()
        ).all()
    )

@app.route('/admin/confirm-booking/<int:booking_id>', methods=['POST'])
def admin_confirm_booking(booking_id):

    if 'admin_id' not in session:

        return redirect(
            url_for('admin_login')
        )

    booking = Booking.query.get(booking_id)

    if not booking:

        return "Booking not found", 404

    if booking.status != 'confirmed':

        booking.status = 'confirmed'

        db.session.commit()

    return redirect(
        url_for('admin_dashboard')
    )

@app.route('/logout')
def logout():

    session.clear()

    return redirect(
        url_for('welcome')
    )

@app.route('/api/tourist-spots')
def api_tourist_spots():

    return jsonify(
        tourist_spots
    )

@app.route('/api/profile')
@token_required
def api_profile(current_user):

    bookings = []

    for booking in current_user.bookings:

        bookings.append({

            'tourist_spot':
            booking.tourist_spot,

            'booking_date':
            booking.booking_date,

            'desired_date':
            booking.desired_date,

            'desired_time':
            booking.desired_time,

            'accommodation_check_in':
            booking.accommodation_check_in,

            'accommodation_check_in_time':
            booking.accommodation_check_in_time,

            'status':
            booking.status
        })

    return jsonify({

        'username':
        current_user.username,

        'contact_number':
        current_user.contact_number,

        'bookings':
        bookings
    })

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
