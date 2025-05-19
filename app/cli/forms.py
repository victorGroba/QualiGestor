from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms_sqlalchemy.fields import QuerySelectField

from app.models import Cliente, Loja, Formulario

# Cadastro de novo formulário
class FormularioForm(FlaskForm):
    nome = StringField('Nome do Formulário', validators=[DataRequired()])
    cliente = QuerySelectField('Cliente', query_factory=lambda: Cliente.query.all(), allow_blank=True, get_label='nome')
    loja = QuerySelectField('Loja', query_factory=lambda: Loja.query.all(), allow_blank=True, get_label='nome')
    submit = SubmitField('Criar Formulário')

# Cadastro de pergunta
class PerguntaForm(FlaskForm):
    texto = StringField('Texto da Pergunta', validators=[DataRequired()])
    tipo_resposta = SelectField('Tipo de Resposta', choices=[
        ('SIM_NAO', 'Sim/Não'),
        ('TEXTO', 'Texto'),
        ('NOTA', 'Nota')
    ], validators=[DataRequired()])
    obrigatoria = BooleanField('Obrigatória', default=True)
    submit = SubmitField('Adicionar Pergunta')
