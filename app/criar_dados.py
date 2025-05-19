from . import create_app
from .models import Formulario, Pergunta, db

app = create_app()

with app.app_context():
    db.create_all()

    if not Formulario.query.first():
        form = Formulario(nome="Checklist de Higiene")
        db.session.add(form)
        db.session.flush()

        perguntas = [
            Pergunta(texto="O ambiente está limpo?", tipo="escolha", formulario_id=form.id),
            Pergunta(texto="Funcionários estão com EPI completo?", tipo="escolha", formulario_id=form.id),
            Pergunta(texto="Temperatura da geladeira está adequada?", tipo="nota", formulario_id=form.id),
            Pergunta(texto="Observações gerais", tipo="texto", formulario_id=form.id),
        ]
        db.session.add_all(perguntas)
        db.session.commit()
        print("✅ Formulário e perguntas criadas com sucesso!")
    else:
        print("⚠️ Já existem formulários no banco.")
