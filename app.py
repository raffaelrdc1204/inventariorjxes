import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras
from datetime import date
from dotenv import load_dotenv
import sys

# Carrega variáveis (importante para teste local)
load_dotenv()

app = Flask(__name__)

# Função de log para monitorarmos o Render em tempo real
def log_debug(mensagem):
    print(f"[DEBUG] {mensagem}", file=sys.stdout, flush=True)

def get_db_connection():
    try:
        # Pega a URL que você acabou de corrigir no Render
        db_url = os.environ.get('DATABASE_URL')
        
        # Fallback de segurança (URL Completa)
        if not db_url:
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"

        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        log_debug(f"ERRO AO CONECTAR NO BANCO: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    log_debug(f"Solicitação recebida para Almoxarifado: {almox}")
    conn = get_db_connection()
    if not conn:
        return jsonify([]) 

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # AQUI ESTÁ O AJUSTE DAS ASPAS E ACENTOS (Crucial para PostgreSQL)
        cursor.execute("""
            SELECT 
                id, 
                "ORIGEM", 
                "PRODUTOS", 
                "UND", 
                quantidade_real, 
                "ultima_atualização" AS ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM("ALMOX")) = UPPER(TRIM(%s))
        """, (almox,))

        dados = cursor.fetchall()
        log_debug(f"Busca finalizada. Encontrados {len(dados)} itens.")

        for item in dados:
            if item.get('ultima_atualizacao'):
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Sem Data'
        
        return jsonify(dados)
    except Exception as e:
        log_debug(f"ERRO NA CONSULTA SQL: {e}")
        return jsonify([])
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/atualizar', methods=['POST'])
def atualizar():
    log_debug("Iniciando atualização de dados...")
    dados = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            # Também usamos aspas e acento no UPDATE
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, "ultima_atualização" = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        log_debug("Dados salvos com sucesso!")
        return jsonify({"status": "sucesso", "mensagem": "Inventário atualizado!"})
    except Exception as e:
        log_debug(f"ERRO AO SALVAR: {e}")
        conn.rollback() 
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

