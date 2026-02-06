import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

app = Flask(__name__)

# Configuração do CORS: Permite que o GitHub Pages acesse este backend
CORS(app, resources={r"/*": {"origins": "*"}})

def log_debug(mensagem):
    print(f"[DEBUG] {mensagem}", file=sys.stdout, flush=True)

def get_db_connection():
    try:
        # Pega a URL do banco das variáveis de ambiente do Render
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # Fallback para a sua string direta (Apenas para teste, não recomendado em produção)
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"
        
        # AJUSTE CRUCIAL: O Render usa 'postgres://', mas o SQLAlchemy/Psycopg2 exige 'postgresql://'
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        # Conexão com SSL obrigatório para o Render
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        log_debug(f"ERRO CRÍTICO DE CONEXÃO: {e}")
        return None

@app.route('/')
def index():
    # Para esta rota funcionar, o index.html DEVE estar dentro de uma pasta chamada 'templates'
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Erro: Arquivo index.html não encontrado na pasta /templates. Detalhe: {e}", 404

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    log_debug(f"Recebendo requisição para o Almoxarifado: {almox}")
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"erro": "Falha ao conectar ao banco de dados"}), 500

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # A busca usa UPPER e TRIM para evitar erros de digitação ou espaços no banco
        # IMPORTANTE: Verifique se a coluna no seu banco se chama exatamente 'almox'
        query = """
            SELECT 
                id, 
                origem, 
                produtos, 
                und, 
                quantidade_real, 
                ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(almox)) = UPPER(TRIM(%s))
            ORDER BY produtos ASC
        """
        cursor.execute(query, (almox,))
        dados = cursor.fetchall()
        
        log_debug(f"Dados encontrados para {almox}: {len(dados)} itens")

        # Formata a data para o padrão brasileiro
        for item in dados:
            if item.get('ultima_atualizacao'):
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
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
        return jsonify({"status": "erro", "mensagem": "Nenhum dado enviado"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão com o banco"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Inventário atualizado!"})
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
