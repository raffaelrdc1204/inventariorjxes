import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2 import extras
from datetime import date
from dotenv import load_dotenv
import sys # Importante para os logs aparecerem no Render

# Carrega variáveis
load_dotenv()

app = Flask(__name__)

# Função para garantir que o log apareça no painel do Render imediatamente
def log_debug(mensagem):
    print(f"[DEBUG] {mensagem}", file=sys.stdout, flush=True)

def get_db_connection():
    try:
        db_url = os.environ.get('DATABASE_URL')
        
        # Fallback local (apague antes de produção final se quiser)
        if not db_url:
             db_url = "postgresql://sgi_inventario_rjxes_sj1y_user:EWE0hyxbbyIrQ300TSmR23GlPHzbgVBu@dpg-d61vdo4r85hc7388e95g-a.ohio-postgres.render.com/sgi_inventario_rjxes_sj1y"

        if not db_url:
            log_debug("ERRO CRÍTICO: Sem URL de conexão.")
            return None

        log_debug("Tentando conectar ao banco...")
        conn = psycopg2.connect(db_url, sslmode='require')
        log_debug("Conexão realizada com sucesso!")
        return conn
    except Exception as e:
        log_debug(f"ERRO AO CONECTAR: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materiais/<almox>')
def listar_materiais(almox):
    log_debug(f"Recebida solicitação para o Almoxarifado: {almox}")
    
    conn = get_db_connection()
    if not conn:
        log_debug("Abortando: Conexão falhou.")
        return jsonify([]) 

    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Removi os "Aliases" (AS "NOME") para testar o padrão nativo.
        # Estamos buscando na tabela correta: inventario_almox_rjxes
        query = """
            SELECT id, ORIGEM, PRODUTOS, UND, quantidade_real, ultima_atualizacao
            FROM inventario_almox_rjxes
            WHERE UPPER(TRIM(ALMOX)) = UPPER(TRIM(%s))
        """
        log_debug(f"Executando Query: {query} com parametro {almox}")
        
        cursor.execute(query, (almox,))
        dados = cursor.fetchall()
        
        log_debug(f"RESULTADO: Encontrados {len(dados)} registros.")

        # Se encontrou dados, vamos imprimir o primeiro para ver as chaves (colunas)
        if len(dados) > 0:
            log_debug(f"Exemplo de registro encontrado: {dados[0]}")

        for item in dados:
            if item.get('ultima_atualizacao'): # .get evita erro se a chave mudar
                item['data_fmt'] = item['ultima_atualizacao'].strftime('%d/%m/%Y')
            else:
                item['data_fmt'] = 'Sem Data'
        
        return jsonify(dados)

    except Exception as e:
        log_debug(f"ERRO GRAVE NA CONSULTA SQL: {e}")
        return jsonify([])
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/atualizar', methods=['POST'])
def atualizar():
    log_debug("Iniciando atualização de inventário...")
    dados = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Sem conexão com o banco"}), 500
    
    cursor = conn.cursor()
    try:
        for item in dados:
            query = """
                UPDATE inventario_almox_rjxes 
                SET quantidade_real = %s, ultima_atualizacao = NOW() 
                WHERE id = %s
            """
            cursor.execute(query, (item['nova_qtd'], item['id']))
        
        conn.commit()
        log_debug("Atualização salva com sucesso.")
        return jsonify({"status": "sucesso", "mensagem": "Inventário atualizado com sucesso!"})
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

