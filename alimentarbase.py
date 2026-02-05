import pandas as pd
import mysql.connector
import re

config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456789', 
    'database': 'inventario_rjxes'
}

def limpar_quantidade(valor):
    """ Remove letras e converte para número. Se for vazio ou inválido, retorna 0. """
    if pd.isna(valor) or str(valor).strip() == "":
        return 0
    # Remove qualquer coisa que não seja número (ex: '2lt' vira '2')
    apenas_numeros = re.sub(r'[^0-9]', '', str(valor))
    return int(apenas_numeros) if apenas_numeros != "" else 0

def alimentar_banco_pelas_abas():
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        print("Conectado ao banco. Iniciando importação...")

        # 1. RIO DE JANEIRO
        xls_rj = pd.ExcelFile('BASE INVENTARIO RJ.xlsx')
        for aba in ['RJO', 'VRD', 'CPS', 'ROS']:
            df = pd.read_excel(xls_rj, sheet_name=aba)
            for _, row in df.iterrows():
                qtd = limpar_quantidade(row['QTD. REAL'])
                sql = "INSERT INTO inventario (ORIGEM, PRODUTOS, UND, ALMOX, UF, quantidade_real) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (row['ORIGEM'], row['PRODUTOS'], row['UND'], aba, 'RJ', qtd))
            print(f"✅ Aba {aba} (RJ) importada.")

        # 2. ESPÍRITO SANTO
        xls_es = pd.ExcelFile('BASE INVENTARIO ES.xlsx')
        for aba in ['VVA', 'CIM', 'CNA', 'LNS']:
            df = pd.read_excel(xls_es, sheet_name=aba)
            for _, row in df.iterrows():
                # No ES, pegamos a última coluna e limpamos o valor
                qtd = limpar_quantidade(row.iloc[-1])
                sql = "INSERT INTO inventario (ORIGEM, PRODUTOS, UND, ALMOX, UF, quantidade_real) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (row['ORIGEM'], row['PRODUTOS'], row['UND'], aba, 'ES', qtd))
            print(f"✅ Aba {aba} (ES) importada.")

        conn.commit()
        print("\n🚀 SUCESSO! O banco de dados está pronto para o uso.")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    alimentar_banco_pelas_abas()