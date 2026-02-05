import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras
from datetime import date

app = Flask(__name__)

# --- CONFIGURAÇÃO DA CONEXÃO ---
# Aqui está a URL que você forneceu. O código vai usá-la quando rodar no seu computador.
# Quando estiver no Render, ele vai ignorar isso e usar a variável de ambiente automática.
URL_CONEXAO_LOCAL = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"

def get_db_connection():
    try:
        # 1. Tenta pegar a variável do sistema (Ambiente do Render)
        db_url = os.environ.get('DATABASE_URL')
        
        # 2. Se não achar (ou seja, está no seu PC), usa a URL fixa que definimos acima
        if not db_url:
            db_url = URL_CONEXAO_LOCAL

        # 3. Conecta com SSL exigido pelo Render
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    conn = get_db_connection()
    if not conn:
        # Retorna lista vazia se não conectar, para não quebrar o front
        return jsonify([]) 

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # CORREÇÃO: Nome da tabela atualizado para 'inventario_almox_rjxes'
    try:
        cursor.execute("""
            SELECT id, ORIGEM, PRODUTOS, UND, quantidade_real, ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(ALMOX)) = UPPER(TRIM(%s))
        """, (almox,))

        dados = cursor.fetchall()

        for item in dados:
            if item['ultima_atualizacao']:
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Sem Data'
        
        return jsonify(dados)
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/atualizar', methods=['POST'])
def atualizar():
    dados = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão com o banco"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            # CORREÇÃO: Nome da tabela atualizado para 'inventario_almox_rjxes'
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Inventário atualizado com sucesso!"})
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        conn.rollback() 
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
