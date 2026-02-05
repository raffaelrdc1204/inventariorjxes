import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import sys

load_dotenv()

app = Flask(__name__)

def log_debug(mensagem):
    print(f"[DEBUG] {mensagem}", file=sys.stdout, flush=True)

def get_db_connection():
    try:
        # Prioriza a variável de ambiente do Render
        db_url = os.environ.get('DATABASE_URL')
        
        # Fallback para sua URL direta caso a variável não esteja configurada
        if not db_url:
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"

        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        log_debug(f"ERRO AO CONECTAR: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    log_debug(f"Buscando Almoxarifado: {almox}")
    conn = get_db_connection()
    if not conn:
        return jsonify([]) 

    # RealDictCursor faz com que os nomes das colunas virem chaves no dicionário Python
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # QUERY LIMPA: Sem aspas e sem acentos
        cursor.execute("""
            SELECT 
                id, 
                origem, 
                produtos, 
                und, 
                quantidade_real, 
                ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(almox)) = UPPER(TRIM(%s))
        """, (almox,))

        dados = cursor.fetchall()
        
        for item in dados:
            if item.get('ultima_atualizacao'):
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Sem Data'
        
        return jsonify(dados)

    except Exception as e:
        log_debug(f"ERRO DE SQL: {e}")
        return jsonify([])
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/atualizar', methods=['POST'])
def atualizar():
    dados = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            # Update usando os novos nomes de coluna
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Atualizado!"})
    except Exception as e:
        log_debug(f"Erro ao salvar: {e}")
        conn.rollback() 
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
