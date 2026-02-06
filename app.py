import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Ajuste o CORS para ser mais permissivo durante os testes
CORS(app, resources={r"/*": {"origins": "*"}}) 

def get_db_connection():
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"
        
        # CORREÇÃO: O psycopg2 exige 'postgresql://' em vez de 'postgres://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"[ERRO] Falha na conexão com o banco: {e}")
        return None

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    conn = get_db_connection()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco"}), 500

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # DICA: Verifique se o nome da coluna no seu banco é realmente 'almox'
        query = """
            SELECT id, origem, produtos, und, quantidade_real, ultima_atualizacao 
            FROM inventario_almox_rjxes 
            WHERE UPPER(TRIM(almox)) = UPPER(TRIM(%s))
            ORDER BY produtos ASC
        """
        cursor.execute(query, (almox,))
        dados = cursor.fetchall()
        
        for item in dados:
            if item.get('ultima_atualizacao'):
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Pendente'
        
        return jsonify(dados)
    except Exception as e:
        print(f"[ERRO] Erro no SQL: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

