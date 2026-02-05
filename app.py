import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db_connection():
    try:
        # Tenta pegar a variável do Render primeiro
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"
        return psycopg2.connect(db_url, sslmode='require')
    except Exception as e:
        print(f"Erro conexao: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    conn = get_db_connection()
    if not conn: return jsonify([])
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # Ordenação fixa para evitar que os itens mudem de posição
        cursor.execute("""
            SELECT id, origem, produtos, und, quantidade_real, ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(almox)) = UPPER(TRIM(%s))
            ORDER BY produtos ASC
        """, (almox,))
        dados = cursor.fetchall()
        for item in dados:
            item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y') if item.get('ultima_atualizacao') else 'Pendente'
        return jsonify(dados)
    finally:
        cursor.close()
        conn.close()

@app.route('/atualizar', methods=['POST'])
def atualizar():
    dados = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"status": "erro"}), 500
    cursor = conn.cursor()
    try:
        for item in dados:
            cursor.execute("""
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """, (item['nova_qtd'], item['id']))
        conn.commit()
        return jsonify({"status": "sucesso"})
    except:
        conn.rollback()
        return jsonify({"status": "erro"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run()


