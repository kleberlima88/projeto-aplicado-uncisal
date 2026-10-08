import os
import requests
from dotenv import load_dotenv

# Carrega a sua chave secreta do ficheiro .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print("A consultar a Groq...")
response = requests.get(url, headers=headers)
dados = response.json()

print("\n--- Modelos disponíveis para a sua chave ---")
if 'data' in dados:
    for modelo in dados['data']:
        print(f"ID exato: {modelo['id']}")
else:
    print("Erro na consulta:", dados)