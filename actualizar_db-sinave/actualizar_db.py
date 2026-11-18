import sqlite3
import pandas as pd

try:
    print("Leyendo archivo Excel...")
    df = pd.read_excel(r'C:\Users\abargas\Desktop\DESCARGA DE DATOS.xlsx', sheet_name='vtab')

    print("Conectando a la base de datos...")
    conexion = sqlite3.connect(r'C:\Users\abargas\Documents\R Studio\SINAVE 2.0-SQLite.db')

    print("Volcando y reemplazando datos en la tabla...")
    # Cambiamos 'append' por 'replace' para que sobrescriba los datos anteriores
    df.to_sql('BD SINAVE', conexion, if_exists='replace', index=False)

    conexion.close()
    print("\n¡Datos reemplazados y cargados correctamente!")

except Exception as e:
    print(f"\nOcurrió un error durante el proceso:\n{e}")

input("\nPresiona Enter para salir...")