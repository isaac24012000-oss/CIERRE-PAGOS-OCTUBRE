import pandas as pd

df = pd.read_excel('CIERRE GASTOS ADMINISTRATIVOS NOVIEMBRE 2025.xlsx', sheet_name='Hoja1')
print('COLUMNAS DISPONIBLES:')
print(df.columns.tolist())
print(f'\n\nPRIMERAS 5 FILAS COMPLETAS:')
print(df.head(5))

