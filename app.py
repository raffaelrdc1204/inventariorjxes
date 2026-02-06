import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# CORS: Permite que seu site no GitHub Pages acesse este backend no Render
CORS(app, resources={r"/*": {"origins": "*"}})

def log_debug(mensagem):
    print(f"[DEBUG] {mensagem}", file=sys.stdout, flush=True)

def get_db_connection():
    try:
        # Pega a URL do banco das variáveis de ambiente do Render
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # Sua string de conexão direta como backup
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"
        
        # Ajuste para garantir que o driver entenda a URL do Render
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        # Conexão com SSL obrigatório para o PostgreSQL no Render
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        log_debug(f"ERRO DE CONEXÃO COM BANCO: {e}")
        return None

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return "Erro: Pasta 'templates' ou arquivo 'index.html' não encontrados.", 404

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    log_debug(f"Buscando Almoxarifado: {almox}")
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"erro": "Falha na conexão"}), 500

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Busca os materiais filtrando pelo almoxarifado selecionado
        query = """
            SELECT id, origem, produtos, und, quantidade_real, ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(almox)) = UPPER(TRIM(%s))
            ORDER BY produtos ASC
        """
        cursor.execute(query, (almox,))
        dados = cursor.fetchall()
        
        log_debug(f"Dados encontrados para {almox}: {len(dados)} itens")

        # --- CORREÇÃO DO ERRO DE DATA ---
        # Resolve o erro: 'str' object has no attribute 'strftime'
        for item in dados:
            val = item.get('ultima_atualizacao')
            if val:
                # Se for um objeto de data real do Python
                if hasattr(val, 'strftime'):
                    item['data_fmt'] = val.strftime('%d/%m/%Y')
                else:
                    # Se o banco já devolveu como texto (string), apenas limpamos o formato
                    # Isso evita que o código tente formatar o que já é texto
                    item['data_fmt'] = str(val).split(' ')[0] 
            else:
                item['data_fmt'] = 'Pendente'
        
        return jsonify(dados)

    except Exception as e:
        log_debug(f"ERRO NO SELECT: {e}")
        return jsonify({"erro": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/atualizar', methods=['POST'])
def atualizar():
    dados = request.json
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Sem dados"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            # Salva a nova contagem e atualiza a data para AGORA (NOW())
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Atualizado!"})
    except Exception as e:
        log_debug(f"ERRO AO SALVAR: {e}")
        if conn:
            conn.rollback() 
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # Porta configurada automaticamente pelo Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

