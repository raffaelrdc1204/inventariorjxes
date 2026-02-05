from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456789", 
            database="inventario_rjxes"
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

from datetime import date

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, ORIGEM, PRODUTOS, UND, quantidade_real, ultima_atualizacao
        FROM inventario
        WHERE UPPER(TRIM(ALMOX)) = UPPER(TRIM(%s))
    """, (almox,))

    dados = cursor.fetchall()

    for item in dados:
        if item['ultima_atualizacao']:
            item['ultima_atualizacao'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
        else:
            item['ultima_atualizacao'] = 'Sem Data'

    cursor.close()
    conn.close()

    return jsonify(dados)




@app.route('/atualizar', methods=['POST'])
def atualizar():
    dados = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            # AJUSTE CHAVE: Forçamos a ultima_atualizacao para a hora de AGORA (NOW())
            query = """
                UPDATE inventario 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Banco de dados atualizado!"})
    except Error as e:
        print(f"Erro ao salvar: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
