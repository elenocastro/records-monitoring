import streamlit as st
import pandas as pd


st.title("📊 Monitoreo de registros")

# Enlace al archivo CSV en Dropbox
egra_url = 'https://www.dropbox.com/scl/fi/pswt5c75c2o2v0csix4mr/EGRA.csv?rlkey=0qzi3sjcs4oklsuncamhz1xt7&dl=1'
docentes_url = 'https://www.dropbox.com/scl/fi/ub2g0606rmqu4ykn4ef15/Docentes.csv?rlkey=3v26fp1cp4tjam3j7si17f5e2&st=aea42d23&dl=1'
docentes_auto_url = 'https://www.dropbox.com/scl/fi/o7fhl9bvp1ey89qdwworu/Docentes-Autoadministrada.csv?rlkey=0a8a8gg61eus8bssvilievbkk&st=86wyxizg&dl=1'
videos_url = 'https://www.dropbox.com/scl/fi/odckndu43clmh948gohfa/videos_teach.xlsx?rlkey=v48p8nw6da2eo36vjg0xntsjq&st=083x6e8q&dl=1'

# Leer el archivo CSV desde Dropbox
egra = pd.read_csv(egra_url)
docentes = pd.read_csv(docentes_url)
docentes_auto = pd.read_csv(docentes_auto_url)
videos = pd.read_excel(videos_url)

# Convertir columnas de fechas a tipo datetime
egra['SubmissionDate'] = pd.to_datetime(egra['SubmissionDate'])
egra['starttime'] = pd.to_datetime(egra['starttime'])

docentes['SubmissionDate'] = pd.to_datetime(docentes['SubmissionDate'])
docentes['starttime'] = pd.to_datetime(docentes['starttime'])

docentes_auto['SubmissionDate'] = pd.to_datetime(docentes_auto['SubmissionDate'])
docentes_auto['starttime'] = pd.to_datetime(docentes_auto['starttime'])

# Crear una nueva columna con solo la fecha (sin la hora)
egra['start_date'] = egra['starttime'].dt.date
docentes['start_date'] = docentes['starttime'].dt.date
docentes_auto['start_date'] = docentes_auto['starttime'].dt.date

videos['Date'] = pd.to_datetime(videos['Date'], format='%Y%m%d')
videos['start_date'] = videos['Date'].dt.date



# Contar el número de encuestas por fecha de inicio
encuestas_por_fecha1 = egra['start_date'].value_counts().sort_index()
encuestas_por_fecha2 = docentes['start_date'].value_counts().sort_index()
encuestas_por_fecha3 = docentes_auto['start_date'].value_counts().sort_index()
encuestas_por_fecha4 = videos['start_date'].value_counts().sort_index()


# Combinar los conteos de los tres DataFrames en un solo DataFrame
encuestas_por_fecha_total = pd.concat([encuestas_por_fecha1, encuestas_por_fecha2, 
                                       encuestas_por_fecha3, encuestas_por_fecha4], axis=1)
encuestas_por_fecha_total.columns = ['EGRA', 'Docentes', 'Docentes-Autoadministrada', 'Videos Teach']
encuestas_por_fecha_total = encuestas_por_fecha_total.fillna(int(0))
encuestas_por_fecha_total = encuestas_por_fecha_total.sort_index(ascending=False)

# Configurar el dashboard
st.header('Número de encuestas subidas por fecha de inicio')
# Convertir el índice a string para que solo muestre la fecha sin la hora
# encuestas_por_fecha_total.index = encuestas_por_fecha_total.index.astype(str)
encuestas_por_fecha1.index = encuestas_por_fecha1.index.astype(str)
encuestas_por_fecha2.index = encuestas_por_fecha2.index.astype(str)
encuestas_por_fecha3.index = encuestas_por_fecha3.index.astype(str)
encuestas_por_fecha4.index = encuestas_por_fecha4.index.astype(str)


# Mostrar el conteo de encuestas por fecha en una tabla
st.dataframe(encuestas_por_fecha_total.style.format("{:.0f}"))

# Calcular los totales para las barras de progreso
totals = encuestas_por_fecha_total.sum(axis=0)
egras_total = totals['EGRA']  # Suponiendo que 'Encuestas1' es EGRA
docentes_total = totals['Docentes'] + totals['Docentes-Autoadministrada']  # Suponiendo que 'Encuestas2' y 'Encuestas3' son docentes y docentes-autoadministradas
videos_total = totals['Videos Teach']  # Restar los otros totales para obtener el total de videos

# Definir las metas
meta_egra = 5000
meta_docentes = 1408
meta_videos = 1408

# Calcular los porcentajes de progreso
progreso_egra = int(egras_total / meta_egra * 100)
progreso_docentes = int(docentes_total / meta_docentes * 100)
progreso_videos = int(videos_total / meta_videos * 100)

# Mostrar las barras de progreso con etiquetas de porcentaje
st.header('Progreso hacia las metas')

st.subheader('EGRA')
st.progress(progreso_egra)
st.write(f'Progreso: {progreso_egra}%')

st.subheader('Docentes (Incluye Docentes y Docentes-Autoadministradas)')
st.progress(progreso_docentes)
st.write(f'Progreso: {progreso_docentes}%')

st.subheader('Videos Teach')
st.progress(progreso_videos)
st.write(f'Progreso: {progreso_videos}%')

# Crear un gráfico de barras para visualizar los datos
st.header('Frecuencia diaria')
st.subheader('EGRA')
st.bar_chart(encuestas_por_fecha1)

# Crear un gráfico de barras para visualizar los datos
st.subheader('Docentes')
st.bar_chart(encuestas_por_fecha2)

# Crear un gráfico de barras para visualizar los datos
st.subheader('Docentes - Autoadministrada')
st.bar_chart(encuestas_por_fecha3)

# Crear un gráfico de barras para visualizar los datos
st.subheader('Videos')
st.bar_chart(encuestas_por_fecha4)