# teste_ia.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega sua chave
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERRO: Chave não encontrada no .env")
else:
    genai.configure(api_key=api_key)
    print(f"Chave configurada: {api_key[:5]}...")

    print("\n--- MODELOS DISPONÍVEIS NA SUA CONTA ---")
    try:
        # Lista tudo que sua chave tem acesso
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        
        print("\n----------------------------------------")
        print("Teste de Geração Simples:")
        # Tenta usar o 1.5 Flash (versão específica)
        model = genai.GenerativeModel('gemini-1.5-flash') 
        response = model.generate_content("Diga 'Olá, funcionou!'")
        print(f"RESPOSTA DA IA: {response.text}")
        
    except Exception as e:
        print(f"\nERRO DETALHADO: {e}")