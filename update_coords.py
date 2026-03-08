import os
import random
from app import create_app, db
from app.models import Avaliado

# Approximate center coordinates for all Brazilian states
STATE_CENTERS = {
    'AC': (-9.0238, -70.8120), 'AL': (-9.5394, -36.7551), 'AP': (1.4192, -51.7792),
    'AM': (-3.4168, -65.8561), 'BA': (-12.5797, -41.7007), 'CE': (-5.4984, -39.3206),
    'DF': (-15.7998, -47.8645), 'ES': (-19.1834, -40.3089), 'GO': (-15.8270, -49.8362),
    'MA': (-4.9609, -45.2744), 'MT': (-12.6819, -56.9211), 'MS': (-20.7722, -54.7852),
    'MG': (-18.5122, -44.5550), 'PA': (-3.2048, -52.3906), 'PB': (-7.2396, -36.7820),
    'PR': (-25.2521, -52.0215), 'PE': (-8.8137, -36.9541), 'PI': (-7.7183, -42.7289),
    'RJ': (-22.9094, -43.2094), 'RN': (-5.4026, -36.9541), 'RS': (-30.0346, -51.2177),
    'RO': (-10.8300, -63.3000), 'RR': (2.7376, -62.0751), 'SC': (-27.2423, -50.2189),
    'SP': (-23.5505, -46.6333), 'SE': (-10.5741, -37.3857), 'TO': (-10.1753, -48.2982),
}

app = create_app()
with app.app_context():
    avaliados = Avaliado.query.all()
    count = 0
    for a in avaliados:
        if not a.estado:
            continue
            
        estado = a.estado.upper()
        if estado in STATE_CENTERS:
            base_lat, base_lng = STATE_CENTERS[estado]
            # Add a random offset between -1.5 and +1.5 degrees so they don't overlap
            rand_lat_offset = random.uniform(-1.5, 1.5)
            rand_lng_offset = random.uniform(-1.5, 1.5)
            
            a.latitude = str(base_lat + rand_lat_offset)
            a.longitude = str(base_lng + rand_lng_offset)
            count += 1
            
    db.session.commit()
    print(f"Succeessfully updated {count} rancho coordinates with random offsets.")
