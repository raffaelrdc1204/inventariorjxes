import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras
from datetime import date
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (para teste local seguro)
load_dotenv()

app = Flask(__name__)

def get_db_connection():
    try:
        # 1. Tenta pegar a URL configurada no Render (Seguro e Automático)
        db_url = os.environ.get('DATABASE_URL')
        
        # --- BLOCO PARA TESTE LOCAL (SE PRECISAR) ---
        # Se não achar a variável (estiver no seu PC sem .env), usa essa fixa.
        # IMPORTANTE: Apague ou comente essa linha antes de subir para o GitHub público!
        if not db_url:
             db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"
        # ---------------------------------------------

        if not db_url:
            print("ERRO CRÍTICO: Nenhuma URL de banco de dados encontrada.")
            return None

        # Conecta com SSL exigido pelo Render
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
        return jsonify([]) 

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # --- AQUI ESTAVA O SEGREDO ---
        # 1. Tabela correta: inventario_almox_rjxes
        # 2. Coluna correta: ALMOX (Pois 'RJO' está na coluna ALMOX, coluna 5)
        cursor.execute("""
            SELECT id, ORIGEM, PRODUTOS, UND, quantidade_real, ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(ALMOX)) = UPPER(TRIM(%s))
        """, (almox,))

        dados = cursor.fetchall()

        # Formata a data para exibir bonitinho no front
        for item in dados:
            if item['ultima_atualizacao']:
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Sem Data'
        
        return jsonify(dados)
    except Exception as e:
        print(f"Erro na consulta SQL: {e}")
        return jsonify([])
    finally:
        # Garante que a conexão fecha mesmo se der erro
        if conn:
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
            # Atualiza a tabela correta
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
    # Usa a porta definida pelo Render ou 5000 localmente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

