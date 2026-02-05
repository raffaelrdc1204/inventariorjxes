import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras
from datetime import date

app = Flask(__name__)

def get_db_connection():
    try:
        # AQUI ESTÁ O TRUQUE: 
        # O código tenta pegar o endereço do banco nas variáveis de ambiente do sistema.
        # Isso é padrão em servidores como o Render.
        db_url = os.environ.get('DATABASE_URL')
        
        if not db_url:
            # Fallback para teste local (opcional, se você instalar Postgres no PC)
            # Se não tiver URL configurada, retorna None para tratarmos o erro.
            print("AVISO: Variável DATABASE_URL não encontrada.")
            return None

        conn = psycopg2.connect(db_url)
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
        # Retorna erro amigável se não conectar (ex: rodando local sem configurar)
        return jsonify([]) 

    # No PostgreSQL, usamos RealDictCursor para receber os dados como dicionário
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # A sintaxe SQL é compatível entre MySQL e Postgres neste caso simples
    cursor.execute("""
        SELECT id, ORIGEM, PRODUTOS, UND, quantidade_real, ultima_atualizacao
        FROM inventario
        WHERE UPPER(TRIM(ALMOX)) = UPPER(TRIM(%s))
    """, (almox,))

    dados = cursor.fetchall()

    for item in dados:
        if item['ultima_atualizacao']:
            item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
        else:
            item['data_fmt'] = 'Sem Data'

    cursor.close()
    conn.close()

    return jsonify(dados)

@app.route('/atualizar', methods=['POST'])
def atualizar():
    dados = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão com o banco"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            # O comando NOW() funciona igual no Postgres
            query = """
                UPDATE inventario 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Inventário atualizado com sucesso!"})
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        # rollback desfaz alterações se der erro no meio do caminho
        conn.rollback() 
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # A porta padrão do Render é definida pela variável PORT, ou usa 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
