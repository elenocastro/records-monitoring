import streamlit as st
import pandas as pd
import numpy as np


st.title("📊 Monitoreo de registros")

# Enlace al archivo CSV en Dropbox
egra_url = 'https://www.dropbox.com/scl/fi/pswt5c75c2o2v0csix4mr/EGRA.csv?rlkey=0qzi3sjcs4oklsuncamhz1xt7&dl=1'
docentes_url = 'https://www.dropbox.com/scl/fi/ub2g0606rmqu4ykn4ef15/Docentes.csv?rlkey=3v26fp1cp4tjam3j7si17f5e2&st=aea42d23&dl=1'
docentes_auto_url = 'https://www.dropbox.com/scl/fi/o7fhl9bvp1ey89qdwworu/Docentes-Autoadministrada.csv?rlkey=0a8a8gg61eus8bssvilievbkk&st=86wyxizg&dl=1'
videos_url = 'https://www.dropbox.com/scl/fi/r8usgt8n0iyshbzklyqcz/videos_teach_long.xlsx?rlkey=eygtkzllp3ng9ouzkprkroquh&st=rax4coo9&dl=1'
docentes_ce_url = 'https://www.dropbox.com/scl/fi/p27k5o7zup7igecfxrjkk/CONTINUIDAD_27062024.xlsx?rlkey=j52pkyf338d1d0ym76igi0440&st=xouj06hu&dl=1'
assignment_ce_url = 'https://www.dropbox.com/scl/fi/uvh67un6k4e6en2yccr7d/assignment_groups_03072023.dta?rlkey=ck70b2ybt7a6hiccpfz5umgwx&st=uud5uifp&dl=1'
docente_per_nie_url = 'https://www.dropbox.com/scl/fi/sribjlu271u6dcoyf0jw7/docente_nie.csv?rlkey=542yce4sqed1wxtds69z4katk&dl=1'

# Leer el archivo CSV desde Dropbox
egra = pd.read_csv(egra_url)
docentes = pd.read_csv(docentes_url)
docentes_auto = pd.read_csv(docentes_auto_url)
videos = pd.read_excel(videos_url)
docentes_ce = pd.read_excel(docentes_ce_url, converters = {'NIE':str, 'unique_id': str})
assignment_ce = pd.read_stata(assignment_ce_url)
docentes_per_nie = pd.read_csv(docente_per_nie_url, converters = {'unique_id': str})

#videos añadiendo unique_id
videos = videos.merge(docentes_ce[['NIP', 'unique_id']].drop_duplicates(), on = 'NIP', how = 'left')


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


# Convertir el índice a string para que solo muestre la fecha sin la hora
# encuestas_por_fecha_total.index = encuestas_por_fecha_total.index.astype(str)
encuestas_por_fecha1.index = encuestas_por_fecha1.index.astype(str)
encuestas_por_fecha2.index = encuestas_por_fecha2.index.astype(str)
encuestas_por_fecha3.index = encuestas_por_fecha3.index.astype(str)
encuestas_por_fecha4.index = encuestas_por_fecha4.index.astype(str)

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

#Contando encuestas por docente

## ANADIENDO docente_id para todos los casos posibles
egra = egra.merge(docentes_per_nie, left_on = 'id_estudiante_nie', right_on = 'per_nie', how = 'left')
egra.rename(columns = {'unique_id': 'docente_administrativo'}, inplace = True)
egra['docente_merge'] = pd.to_numeric(egra['docente'], errors='coerce', downcast='integer')
egra.loc[egra.docente.isna(), 'docente_merge'] = egra.loc[egra.docente.isna(), 'docente_administrativo']
egra['docente_merge'] = pd.to_numeric(egra['docente_merge'], errors='coerce', downcast='integer')

#contando por docente
egra_x_doc = egra.docente_merge.value_counts()
doc_x_doc = docentes.docente.value_counts()
docentes_auto_x_doc = docentes_auto['docente'].value_counts()
videos_doc = videos['unique_id'].value_counts()

egra_x_doc.index = egra_x_doc.index.astype(int)
doc_x_doc.index = doc_x_doc.index.astype(int)
docentes_auto_x_doc.index = docentes_auto_x_doc.index.astype(int)
videos_doc.index = videos_doc.index.astype(int)

#anexando por docente
data_doc = pd.concat([egra_x_doc, doc_x_doc, docentes_auto_x_doc, videos_doc], axis = 1)
data_doc.columns = ['E', 'D', 'DA', 'V'] 

#ajustando index
data_doc.reset_index(inplace = True)
data_doc.rename(columns = {'index': 'unique_id'},inplace = True)
docentes_ce['unique_id'] = docentes_ce['unique_id'].astype(int)

#añadiendo nombre y centro
data_doc = data_doc.merge(docentes_ce[['unique_id', 'NIP',  'Código', 'Nombre_Docente']],
               on = 'unique_id', how = 'left')
data_doc = data_doc.set_index(['unique_id', 'NIP','Código', 'Nombre_Docente' ]).fillna(0)

tab1, tab2, tab3, tab4 = st.tabs(["Por Fecha", "Por Centro Educativo", 
                      'Por Grupo de Tratamiento', 'Por Docente'])


with tab1:
    # Mostrar las barras de progreso con etiquetas de porcentaje
    st.header('Progreso hacia las metas')

    st.write(f'EGRA. Progreso: {progreso_egra}% - ({int(egras_total)}/{meta_egra})')
    st.progress(progreso_egra)
    #st.write(f'Progreso: {progreso_egra}% - ({int(egras_total)}/{meta_egra})')

    st.write(f'Docentes. Progreso: {progreso_docentes}% - ({int(docentes_total)}/{meta_docentes})')
    st.progress(progreso_docentes)
    #st.write(f'Progreso: {progreso_docentes}% - ({int(docentes_total)}/{meta_docentes})')

    st.write(f'Videos Teach. Progreso: {progreso_videos}% - ({int(videos_total)}/{meta_videos})')
    st.progress(progreso_videos)
    #st.write(f'Progreso: {progreso_videos}% - ({int(videos_total)}/{meta_videos})')

    # Configurar el dashboard
    st.header('Número de encuestas subidas por fecha de inicio')
    # Mostrar el conteo de encuestas por fecha en una tabla
    st.dataframe(encuestas_por_fecha_total.style.format("{:.0f}"))

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


## Total de datos a nivel de centro educativo

docentes_auto = docentes_auto.merge(docentes_ce[['Código', 'unique_id']], left_on = 'docente', right_on = 'unique_id', how = 'left')
docentes = docentes.merge(docentes_ce[['Código', 'unique_id']], left_on = 'docente', right_on = 'unique_id', how = 'left')

#contando encuetas a nivel de centro educativo
egra_x_ce = egra['School'].value_counts()
docentes_x_ce = docentes['Código'].value_counts()
docentes_auto_x_ce = docentes_auto['Código'].value_counts()
videos_ce = videos[videos['Name Valid']]['CE en Continuidad'].value_counts()

encuestas_ce = pd.concat([egra_x_ce, docentes_x_ce, docentes_auto_x_ce, videos_ce], axis = 1)
encuestas_ce.columns = ['E', 'D', 'DA', 'V'] 
encuestas_ce = encuestas_ce.fillna(0)
ce = docentes_ce[['Código', 'Centroeducativo', 'Latitud', 'Longitud']].drop_duplicates()

#asignando geo
encuestas_ce = ce.merge(encuestas_ce, right_index = True, left_on = ['Código'], how = 'right')
#asignando tratamiento
encuestas_ce = encuestas_ce.merge(assignment_ce[['treatment', 'Código']], on = 'Código', how= 'left')
encuestas_ce.set_index(['Código', 'Centroeducativo'], inplace = True)

with tab2:
    st.header('Número de encuestas por Centro Educativo')
    st.write('E - EGRA')
    st.write('D - Docentes')
    st.write('DA - Docentes - Autoadministrados')
    st.write('V - Videos')
    
    # Añadir buscador para filtrar por centro educativo
    search_term = st.text_input('Buscar por Centro Educativo')
    if search_term:
        filtered_data = encuestas_ce[encuestas_ce.index.get_level_values('Centroeducativo').str.contains(search_term, case=False)]
    else:
        filtered_data = encuestas_ce
    
    # Convertir los valores a enteros
    filtered_data = filtered_data[['E', 'D', 'DA', 'V']].astype(int)
    st.dataframe(filtered_data)

    # Mostrar el mapa
    st.header('Mapa de Centros Educativos Encuestados')

    mapa_data = encuestas_ce.loc[(encuestas_ce.Latitud != 0), ['Latitud', 'Longitud']]
    mapa_data.columns = ['lat', 'lon']
    mapa_data.dropna(inplace = True)
    mapa_data.drop_duplicates(inplace = True)
    st.map(mapa_data)


# Metas
metas = {
    "Control": 274,
    "Training only": 293,
    "Training+FUSAL": 298,
    "Training+GP": 277,
    "Training+Nudges": 266
}

encuestas_ce['DT'] = encuestas_ce[['D','DA']].sum(axis = 1)
encuestas_tratamiento = encuestas_ce.groupby(['treatment'])[['E','DT','V']].sum()
# st.table(encuestas_tratamiento.astype(int))

with tab3:
    st.header("Progreso por Categoría")

    # Para EGRA (Meta: 1000 para cada grupo)
    st.subheader("EGRA")
    for grupo in encuestas_tratamiento.index:
        progreso_egra = int((encuestas_tratamiento.loc[grupo, 'E'] / 1000) * 100)
        progreso_egra_d = np.round((encuestas_tratamiento.loc[grupo, 'E'] / 1000) * 100,1)
        st.text(f"{grupo}: {progreso_egra_d}% - ({int(encuestas_tratamiento.loc[grupo, 'E'])}/1000)")
        st.progress(progreso_egra)

    # Para Docentes (Meta: específica para cada grupo)
    st.subheader("Docentes")
    for grupo in encuestas_tratamiento.index:
        meta_docentes = metas[grupo]
        progreso_docentes = int((encuestas_tratamiento.loc[grupo, 'DT'] / meta_docentes) * 100)
        progreso_docentes_d = np.round((encuestas_tratamiento.loc[grupo, 'DT'] / meta_docentes * 100),1)
        st.text(f"{grupo}: {progreso_docentes_d}% - ({int(encuestas_tratamiento.loc[grupo, 'DT'])}/{meta_docentes})")
        st.progress(progreso_docentes)

    # Para Videos (Meta: específica para cada grupo)
    st.subheader("Videos")
    for grupo in encuestas_tratamiento.index:
        meta_videos = metas[grupo]
        progreso_videos = int((encuestas_tratamiento.loc[grupo, 'V'] / meta_videos) * 100)
        progreso_videos_d = np.round((encuestas_tratamiento.loc[grupo, 'V'] / meta_videos * 100),1)
        st.text(f"{grupo}: {progreso_videos_d}% - ({int(encuestas_tratamiento.loc[grupo, 'V'])}/{meta_videos})")
        st.progress(progreso_videos)

with tab4:
    st.header('Número de encuestas por Docente')
    st.write('E - EGRA')
    st.write('D - Docentes')
    st.write('DA - Docentes - Autoadministrados')
    st.write('V - Videos')
    
    # Añadir buscador para filtrar por centro educativo
    search_term = st.text_input('Buscar por Docente')
    if search_term:
        filtered_data = data_doc[data_doc.index.get_level_values('Nombre_Docente').str.contains(search_term, case=False)]
    else:
        filtered_data = data_doc
    
    # Convertir los valores a enteros
    filtered_data = filtered_data[['E', 'D', 'DA', 'V']].astype(int)
    st.dataframe(filtered_data)


    st.header('Estudiantes sin docente')

    sin_nie = egra.loc[egra.docente_merge.isna(),['starttime','encuestador','School', 'id_estudiante_nie']]
    st.dataframe(sin_nie)