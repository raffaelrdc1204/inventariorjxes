from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import date

app = Flask(__name__)

def get_db_connection():
    try:
        # ATENÇÃO: Essas credenciais funcionam apenas no seu PC (Localhost).
        # Para subir no Render, precisaremos mudar isso depois.
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

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    conn = get_db_connection()
    if not conn:
        return jsonify([]) # Retorna lista vazia se não conectar

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, ORIGEM, PRODUTOS, UND, quantidade_real, ultima_atualizacao
        FROM inventario
        WHERE UPPER(TRIM(ALMOX)) = UPPER(TRIM(%s))
    """, (almox,))

    dados = cursor.fetchall()

    for item in dados:
        # AJUSTE IMPORTANTE: Criando o campo 'data_fmt' que o HTML espera
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
            # Atualiza a quantidade e define a hora atual (NOW())
            query = """
                UPDATE inventario 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        return jsonify({"status": "sucesso", "mensagem": "Inventário atualizado com sucesso!"})
    except Error as e:
        print(f"Erro ao salvar: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
