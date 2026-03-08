import os
from app import create_app, db
from app.models import Avaliado
app = create_app()
with app.app_context():
    avaliados = Avaliado.query.all()
    for a in avaliados:
        print(f"ID={a.id} NOME={a.nome} ESTADO={a.estado} LAT={a.latitude} LNG={a.longitude}")
