from flask import Flask, render_template, request, flash, redirect, session
from werkzeug.utils import secure_filename
from functools import wraps
import os
import json
import csv
import html
from datetime import datetime
from dotenv import load_dotenv
import markdown
from markupsafe import Markup

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Lemos a chave da Groq do ficheiro .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

try:
    from openai import OpenAI
    HAS_OPENAI = True
    # Configuramos o cliente para usar os servidores da Groq em vez da OpenAI ou DeepSeek
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
except Exception:
    OpenAI = None
    HAS_OPENAI = False
    client = None

try:
    import pandas as pd
    HAS_PANDAS = True
except Exception:
    pd = None
    HAS_PANDAS = False

app = Flask(__name__)
app.secret_key = "chave_super_secreta_projeto_uncisal" 

# --- CINTURÃO DE SEGURANÇA (OWASP TOP 10) ---
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

ARQUIVO_USUARIO = 'dados_usuario.json'

def carregar_dados_usuario():
    if os.path.exists(ARQUIVO_USUARIO):
        with open(ARQUIVO_USUARIO, 'r') as f:
            return json.load(f)
    return {"ultimo_teste_cooper": None, "historico_vam": []}

# --- MITIGAÇÃO OWASP: Controle de Acesso Quebrado ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logado' not in session:
            flash('Acesso negado. Por favor, faça login para acessar o painel.', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE AUTENTICAÇÃO (EIXO 3) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        
        # Mitigação OWASP (Injeção): Validação estrita sem concatenação
        if usuario == 'admin' and senha == 'triatlo2026':
            session['logado'] = True
            return redirect('/')
        else:
            flash('Credenciais inválidas. Tente novamente.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logado', None)
    flash('Você saiu do sistema com sucesso.', 'success')
    return redirect('/login')

# --- ROTAS PROTEGIDAS ---
@app.route('/')
@login_required # Proteção ativada
def painel_treinamento():
    dados = carregar_dados_usuario()
    precisa_novo_teste = False
    mensagem_status = ""

    if not dados["ultimo_teste_cooper"]:
        precisa_novo_teste = True
        mensagem_status = "Bem-vindo à periodização! Para iniciarmos, realize o Teste de Cooper de 12 minutos."
    else:
        data_ultimo_teste = datetime.strptime(dados["ultimo_teste_cooper"], "%Y-%m-%d")
        dias_passados = (datetime.now() - data_ultimo_teste).days
        if dias_passados >= 90:
            precisa_novo_teste = True
            mensagem_status = f"Fim do Macrociclo! Já se passaram {dias_passados} dias. É hora de recalibrar seu pace."
        else:
            mensagem_status = f"Macrociclo ativo. Faltam {90 - dias_passados} dias para a sua próxima reavaliação."

    return render_template('painel.html', precisa_novo_teste=precisa_novo_teste, mensagem_status=mensagem_status)

@app.route('/upload', methods=['POST'])
@login_required # Proteção ativada
def upload_file():
    if 'file' not in request.files:
        flash('Nenhum arquivo detectado pelo sistema.', 'error')
        return redirect('/')
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Nenhum arquivo foi selecionado.', 'error')
        return redirect('/')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        caminho_salvo = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(caminho_salvo)
        
        try:
            if HAS_PANDAS and pd is not None:
                df = pd.read_csv(caminho_salvo)
                distancia_total = df['Distância'].sum() if 'Distância' in df.columns else "8.00"
                fc_maxima = df['FC Máxima'].max() if 'FC Máxima' in df.columns else "187"
                fc_media = df['FC Média'].mean() if 'FC Média' in df.columns else "175"
                tabela_html = df.head().to_html(classes='tabela-garmin', escape=True)
            else:
                encoding = "utf-8-sig"
                try:
                    with open(caminho_salvo, "r", encoding="utf-8-sig") as f:
                        f.read(1024)
                except UnicodeDecodeError:
                    encoding = "latin-1"

                with open(caminho_salvo, "r", encoding=encoding, newline="") as f:
                    reader = csv.reader(f)
                    rows = list(reader)

                headers = rows[0] if rows else []
                data_rows = rows[1:6] if len(rows) > 1 else []

                headers_lower = [h.strip().lower() for h in headers]
                dist_idx = next((i for i, h in enumerate(headers_lower) if "dist" in h), None)
                fc_max_idx = next((i for i, h in enumerate(headers_lower) if "fc" in h and ("máx" in h or "max" in h)), None)
                fc_med_idx = next((i for i, h in enumerate(headers_lower) if "fc" in h and ("méd" in h or "med" in h)), None)

                def parse_num(val):
                    try:
                        return float(val.strip().replace(",", "."))
                    except (ValueError, AttributeError):
                        return None

                all_data = rows[1:] if len(rows) > 1 else []
                dists = [parse_num(r[dist_idx]) for r in all_data if dist_idx is not None and dist_idx < len(r)]
                dists = [d for d in dists if d is not None]
                distancia_total = f"{sum(dists):.2f}" if dists else "8.00"

                fc_maxs = [parse_num(r[fc_max_idx]) for r in all_data if fc_max_idx is not None and fc_max_idx < len(r)]
                fc_maxs = [f for f in fc_maxs if f is not None]
                fc_maxima = f"{int(max(fc_maxs))}" if fc_maxs else "187"

                fc_meds = [parse_num(r[fc_med_idx]) for r in all_data if fc_med_idx is not None and fc_med_idx < len(r)]
                fc_meds = [f for f in fc_meds if f is not None]
                fc_media = f"{sum(fc_meds)/len(fc_meds):.1f}" if fc_meds else "175"

                th_html = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
                tb_html = "".join("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in r) + "</tr>" for r in data_rows)
                tabela_html = f'<table class="tabela-garmin"><thead><tr>{th_html}</tr></thead><tbody>{tb_html}</tbody></table>'
            
            # --- LÓGICA DE NEGÓCIO E PROMPTS MESTRES ---
            dados_usuario = carregar_dados_usuario()
            
            if not dados_usuario.get("ultimo_teste_cooper"):
                prompt_ia = f"""
Atue como um treinador especialista em periodização de corrida e triatlo.
O atleta realizou um Teste de Cooper inicial com os seguintes resultados:
- Distância: {distancia_total} km
- Frequência Cardíaca Máxima: {fc_maxima} bpm
- Frequência Cardíaca Média: {fc_media} bpm

O objetivo principal do atleta é concluir provas de longa distância.
Ele tem disponibilidade para treinar 4 dias por semana.
Inicie a contagem de um macrociclo de 90 dias a partir de hoje.
Com base nestes dados fisiológicos, gere a primeira planilha semanal de treinos dividindo os dias em tiros, regenerativo e longão.
Regra do Sistema: Informe ao atleta que esta planilha cobrirá toda a semana e uma nova rotina só será recalculada no próximo domingo.
"""
                dados_usuario["ultimo_teste_cooper"] = datetime.now().strftime("%Y-%m-%d")
                with open(ARQUIVO_USUARIO, 'w') as f:
                    json.dump(dados_usuario, f)
            else:
                prompt_ia = f"""
Atue como um treinador especialista em periodização. 
Dados: {distancia_total} km | FC Máx: {fc_maxima} bpm | FC Média: {fc_media} bpm.

Aplique estas duas regras:
Regra 1: Se a FC Média indicar fadiga excessiva, sugira microciclo regenerativo focado em Z2.
Regra 2: Se o treino foi eficiente, aplique sobrecarga de 10% no volume do próximo treino longo.

DIRETRIZ ESTRITA DE RESPOSTA (ECONOMIA DE TOKENS):
1. Dê o diagnóstico e a regra aplicada em no máximo 3 frases curtas. Não explique cálculos matemáticos.
2. Vá diretamente para a geração da tabela Markdown contendo os 7 dias da próxima semana.
3. Não escreva nenhuma introdução, conclusão ou nota de rodapé após a tabela. 
"""

            # Conexão com a API da Groq (Modelo Qwen)
            # --- SISTEMA DE CONTINGÊNCIA (FALLBACK AUTOMÁTICO) ---
            modelos_seguros = [
                "qwen/qwen3.8-27b",
                "openai/gpt-oss-20b"
            ]
            
            analise_ia = None
            
            for modelo_tentativa in modelos_seguros:
                try:
                    if HAS_OPENAI and client is not None:
                        resposta = client.chat.completions.create(
                            model=modelo_tentativa,
                            messages=[{"role": "user", "content": prompt_ia}],
                            max_tokens=980
                        )
                        analise_ia = resposta.choices[0].message.content
                        break  # Sucesso! Interrompe a busca por outros modelos.
                    else:
                        import urllib.request
                        req = urllib.request.Request(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {GROQ_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            data=json.dumps({
                                "model": modelo_tentativa,
                                "messages": [{"role": "user", "content": prompt_ia}],
                                "max_tokens": 980
                            }).encode("utf-8")
                        )
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            dados_resp = json.loads(resp.read().decode("utf-8"))
                            analise_ia = dados_resp["choices"][0]["message"]["content"]
                            break  # Sucesso! Interrompe a busca por outros modelos.
                            
                except Exception as e_ia:
                    print(f"Aviso interno: Falha no modelo {modelo_tentativa}. A tentar o próximo da lista...")
                    continue 

            if not analise_ia:
                flash('Aviso do Sistema: As redes de Inteligência Artificial estão indisponíveis no momento.', 'error')

            # Converte o texto Markdown da IA para formatação HTML real no Flask
            if analise_ia:
                analise_html = Markup(markdown.markdown(analise_ia, extensions=['tables']))
            else:
                analise_html = None

            return render_template('analise.html', prompt=prompt_ia, resposta=analise_html, tabela=tabela_html)
            
        except Exception as e:
            flash(f'Erro ao processar os dados da planilha: {str(e)}', 'error')
            return redirect('/')
            
    else:
        flash('Bloqueio de Segurança: Apenas arquivos .csv são permitidos.', 'error')
        return redirect('/')

if __name__ == '__main__':
    # Mitigação OWASP (Security Misconfiguration): debug desativado para produção
    app.run(debug=False)