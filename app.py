import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Importante para rodar o HTML no GitHub
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permite que o GitHub Pages acesse o backend no Render

def log_debug(mensagem):
    print(f"[DEBUG] {mensagem}", file=sys.stdout, flush=True)

def get_db_connection():
    try:
        # Prioriza a URL do Render, com fallback para a string direta
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"
        
        # Conexão com SSL obrigatório para o Render
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        log_debug(f"ERRO DE CONEXÃO: {e}")
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

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # A ORDENAÇÃO (ORDER BY) evita que os itens pulem para o fim da tabela
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
            ORDER BY produtos ASC
        """, (almox,))

        dados = cursor.fetchall()
        
        # Formata a data para exibição no front-end
        for item in dados:
            if item.get('ultima_atualizacao'):
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Pendente'
        
        return jsonify(dados)

    except Exception as e:
        log_debug(f"ERRO DE SQL NO SELECT: {e}")
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
            # Atualiza usando os nomes de coluna padronizados
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Atualizado com sucesso!"})
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
    # Porta configurada para o Render ou padrão 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

