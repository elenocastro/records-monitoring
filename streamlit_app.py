import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
import statsmodels.api as sm
import plotly.graph_objects as go


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
#videos = videos.merge(docentes_ce[['NIP', 'unique_id']].drop_duplicates(), on = 'NIP', how = 'left')


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

# Encontrando EGRA invalidos
# Principal razon: Los encuestador no terminan la prueba en un minuto a pesar de que el estudiante no se equivoca en primeros items

first_line  = {'letter': [f'letters_{i}' for i in range(1, 11)], 
'nonwords': [f'nonwords_{i}' for i in range(1, 6)],
'reading': [f'reading_{i}' for i in range(1, 11)],}

sections = ['letter', 'nonwords', 'reading']

for section in sections:
    egra[section + '_invalid'] = 0
    cond1 = egra[ section + '_time'] >= 10
    cond2 = (egra[first_line[section]].mean(axis = 1) != 1)
    
    egra.loc[cond1 & cond2, section + '_invalid'] = 1

egra['Invalid'] = (egra[egra.columns[egra.columns.str.contains('invalid')]].sum(axis=1)>0)*1


#Contando encuestas por docente

## ANADIENDO docente_id para todos los casos posibles
egra = egra.merge(docentes_per_nie, left_on = 'id_estudiante_nie', right_on = 'per_nie', how = 'left')
egra.rename(columns = {'unique_id': 'docente_administrativo'}, inplace = True)
egra['docente_merge'] = pd.to_numeric(egra['docente'], errors='coerce', downcast='integer')
egra.loc[egra.docente.isna(), 'docente_merge'] = egra.loc[egra.docente.isna(), 'docente_administrativo']
egra['docente_merge'] = pd.to_numeric(egra['docente_merge'], errors='coerce', downcast='integer')

#Filtrando y dejando solo validos
egra_invalid = egra[egra.Invalid == 1]
egra = egra[egra.Invalid == 0]

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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Por Fecha", "Por Centro Educativo", 
                      'Por Grupo de Tratamiento', 'Por Docente', 'Inconsistencias', 'NIEs x Docente', 'Invalidos'])


# Revisando attrition por grupo
docentes_ce = docentes_ce.merge(data_doc.reset_index()[['unique_id', 'E', 'D', 'DA', 'V']], on = 'unique_id', how = 'left')
data_ava = ['E', 'D', 'DA', 'V']
docentes_ce[data_ava] = docentes_ce[data_ava].fillna(0)
docentes_ce['DT'] = docentes_ce[['D', 'DA']].sum(axis = 1)
docentes_ce[['Ei','DTi','Vi']] = (docentes_ce[['E','DT','V']] > 0)*1
docentes_ce_reg = docentes_ce[['Ei','DTi','Vi','Tratamiento', 'Código']]

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

def run_clustered_regression(df, dependent_var, cluster_var='Código'):
    model = ols(f'{dependent_var} ~ Tratamiento', data=df).fit(cov_type='cluster', cov_kwds={'groups': df[cluster_var]})
    return model

# Realizar la regresión para cada variable
models = {}
variables = ['Ei', 'DTi', 'Vi']

for var in variables:
    models[var] = run_clustered_regression(docentes_ce_reg, var)

# Obtener promedios y CI para graficar
def get_means_and_ci(model):
    intercept = model.params['Intercept']
    treatment_groups = model.params.index  # Incluye el intercepto
    means = model.params
    ci = model.conf_int()
    #means['Intercept'] = intercept
    #ci.loc['Intercept'] = [intercept, intercept]
    return means, ci

results = {}

for var in variables:
    means, ci = get_means_and_ci(models[var])
    results[var] = pd.DataFrame({
        'mean': means,
        'ci_lower': ci[0],
        'ci_upper': ci[1]
    })
    results[var].loc[results[var].index != 'Intercept'] += results[var].loc['Intercept', 'mean']

old_keys = ['Ei', 'DTi', 'Vi']
new_keys = ['EGRAs', 'Docentes', 'Videos']

for kn, ko in zip(new_keys, old_keys):
    results[kn] = results[ko]
    del results[ko]
    results[kn].rename(index = {'Intercept': 'Control'}, inplace = True)

# Crear gráficos con plotly
def create_bar_plot(results, variable):
    data = results[variable]
    fig = go.Figure()
    
    for index, row in data.iterrows():
        fig.add_trace(go.Bar(
            x=[row['mean'] * 100],  # Convertir a porcentaje
            y=[index],
            orientation='h',
            error_x=dict(
                type='data',
                array=[(row['ci_upper'] - row['mean']) * 100],  # Convertir a porcentaje
                arrayminus=[(row['mean'] - row['ci_lower']) * 100]  # Convertir a porcentaje
            ),
            marker_color='lightblue',  # Color de las barras
            text=[f'{row["mean"] * 100:.2f}%'],  # Información del hover
            textposition= "none",  # Posición del texto
            hoverinfo='text'  # Mostrar solo el texto
        ))

    fig.update_layout(
        title=f'{variable}',
        xaxis_title='Porcentaje',
        xaxis=dict(range=[0, 100]),  # Rango de 0 a 100
        barmode='group'
    )

    # set showlegend property by name of trace
    for trace in fig['data']: 
        trace['showlegend'] = False

    return fig

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
    st.header("Progreso por Grupo de Tratamiento")

    # Para EGRA (Meta: 1000 para cada grupo)
    #st.subheader("EGRA")
    #for grupo in encuestas_tratamiento.index:
    #    progreso_egra = int((encuestas_tratamiento.loc[grupo, 'E'] / 1000) * 100)
    #    progreso_egra_d = np.round((encuestas_tratamiento.loc[grupo, 'E'] / 1000) * 100,1)
    #    st.text(f"{grupo}: {progreso_egra_d}% - ({int(encuestas_tratamiento.loc[grupo, 'E'])}/1000)")
    #    st.progress(progreso_egra)

    # Para Docentes (Meta: específica para cada grupo)
    #st.subheader("Docentes")
    #for grupo in encuestas_tratamiento.index:
    #    meta_docentes = metas[grupo]
    #    progreso_docentes = int((encuestas_tratamiento.loc[grupo, 'DT'] / meta_docentes) * 100)
    #    progreso_docentes_d = np.round((encuestas_tratamiento.loc[grupo, 'DT'] / meta_docentes * 100),1)
    #    st.text(f"{grupo}: {progreso_docentes_d}% - ({int(encuestas_tratamiento.loc[grupo, 'DT'])}/{meta_docentes})")
    #    st.progress(progreso_docentes)

    # Para Videos (Meta: específica para cada grupo)
    #st.subheader("Videos")
    #for grupo in encuestas_tratamiento.index:
    #    meta_videos = metas[grupo]
    #    progreso_videos = int((encuestas_tratamiento.loc[grupo, 'V'] / meta_videos) * 100)
    #    progreso_videos_d = np.round((encuestas_tratamiento.loc[grupo, 'V'] / meta_videos * 100),1)
    #    st.text(f"{grupo}: {progreso_videos_d}% - ({int(encuestas_tratamiento.loc[grupo, 'V'])}/{meta_videos})")
    #    st.progress(progreso_videos)

    # Aplicación de Streamlit
    #st.title('Análisis de Attrition en RCT')

    for var in new_keys:
        #st.subheader(f'Gráfico para {var}')
        fig = create_bar_plot(results, var)
        st.plotly_chart(fig)

with tab4:

    # Mostrar las barras de progreso con etiquetas de porcentaje
    
    cond1 = (data_doc['E'] != 0)
    cond2 = ~(((data_doc['D'] == 0) & (data_doc['DA'] == 0)))
    cond2 = data_doc[['D', 'DA']].sum(axis = 1) != 0
    cond3 = (data_doc['V'] != 0)

    n_completo = len(data_doc[cond1 & cond2 & cond3])
    n_egras = len(data_doc[data_doc['E'] == 0])
    n_encu = len(data_doc[(data_doc['D'] == 0) & (data_doc['DA'] == 0)])
    n_video = len(data_doc[data_doc['V'] == 0])
    total_doc = len(data_doc)

    st.header('Docentes con data completa:')
    por_n_completo = int(n_completo/len(data_doc) * 100)
    st.write(f'Docentes completos: {por_n_completo}% - ({int(n_completo)}/{total_doc})')
    st.progress(por_n_completo)

    st.header('Docentes con data incompleta:')
    por_n_egras = int(n_egras/len(data_doc) * 100)
    por_n_encu = int(n_encu/len(data_doc) * 100)
    por_n_video = int(n_video/len(data_doc) * 100)

    st.write(f'Docentes sin Egras: {por_n_egras}% - ({int(n_egras)}/{total_doc})')
    st.progress(por_n_egras)
    #st.write(f'Progreso: {progreso_egra}% - ({int(egras_total)}/{meta_egra})')

    st.write(f'Docentes sin Encuestas: {por_n_encu}% - ({int(n_encu)}/{total_doc})')
    st.progress(por_n_encu)
    #st.write(f'Progreso: {progreso_docentes}% - ({int(docentes_total)}/{meta_docentes})')

    st.write(f'Docentes sin Vídeos: {por_n_video}% - ({int(n_video)}/{total_doc})')
    st.progress(por_n_video)
    #st.write(f'Progreso: {progreso_videos}% - ({int(videos_total)}/{meta_videos})')


    st.header('Número de encuestas por Docente')
    st.write('E - EGRA')
    st.write('D - Docentes')
    st.write('DA - Docentes - Autoadministrados')
    st.write('V - Videos')
    
    # Añadir buscador para filtrar por centro educativo
    search_doc = st.text_input('Buscar por Docente')
    search_school = st.text_input('Buscar por Escuela [usar código sin comas, ej: 11135]')
    if search_doc or search_school:
        if search_doc:
            cond1 = data_doc.index.get_level_values('Nombre_Docente').str.contains(search_doc, case=False)
        else:
            cond1 = True
        if search_school:
            cond2 = data_doc.index.get_level_values('Código') == np.int32(search_school)
        else:
            cond2 = True
        filtered_data = data_doc[cond1 & cond2]
    else:
        filtered_data = data_doc
    
    # Convertir los valores a enteros
    filtered_data = filtered_data[['E', 'D', 'DA', 'V']].astype(int)
    st.dataframe(filtered_data)

    
    st.header(f'Docentes Completos')
    st.write('Filtrar datos:')
    Con_EGRAS = st.checkbox('Docentes con EGRAs', value = True)
    Con_Encuestas = st.checkbox('Docentes con Encuestas', value = True)
    Con_Videos = st.checkbox('Docentes con Vídeos', value = True)

    cond_egras = (data_doc['E'] != 0) if Con_EGRAS else (data_doc['E'] == 0)
    cond_encuestas = (data_doc[['D', 'DA']].sum(axis = 1) != 0) if Con_Encuestas else (data_doc[['D', 'DA']].sum(axis = 1) == 0)
    cond_videos = (data_doc['V'] != 0) if Con_Videos else (data_doc['V'] == 0)

    st.dataframe(data_doc[cond_egras & cond_encuestas & cond_videos])


with tab5:
    
    st.subheader('Estudiantes sin docente')
    sin_id_doc = egra.loc[egra.docente_merge.isna(),['starttime','encuestador','School', 'id_estudiante_nie']]
    sin_id_doc.set_index(['id_estudiante_nie'], inplace = True)
    st.dataframe(sin_id_doc)

    
    duplicados = egra[egra.id_estudiante_nie.duplicated(keep = False)]
    duplicados = duplicados[['id_estudiante_nie', 'School', 'starttime', 'encuestador', 'context_est_1', 'context_est_2', 'KEY']]
    duplicados.rename(columns = {'context_est_1': 'Género', 
                                 'context_est_2': 'Edad',
                                 'startime': 'Fecha'}, inplace = True)
    duplicados.set_index(['starttime', 'id_estudiante_nie'], inplace = True)
    st.subheader('Duplicados')
    st.dataframe(duplicados)


with tab6:

    st.header('NIEs por Docentes')

    docentes_nie = egra.merge(docentes_ce[['unique_id', 'Nombre_Docente', 'Código', 'Centroeducativo']],
               left_on = 'docente_merge', right_on = 'unique_id', how = 'left')
    docentes_nie['nie_duplicado'] = docentes_nie.id_estudiante_nie.duplicated(keep = False)
    docentes_nie = docentes_nie[['id_estudiante_nie', 'unique_id', 'Nombre_Docente', 'Código', 'nie_duplicado']]
    docentes_nie.set_index(['id_estudiante_nie', 'Nombre_Docente'], inplace = True)
    
    # Añadir buscador para filtrar por centro educativo
    search_doc2 = st.text_input('Buscar por Docente ')
    search_school2 = st.text_input('Buscar por Código de Escuela [usar código sin comas, ej: 11135]')
    if search_doc2 or search_school2:
        if search_doc2:
            cond1 = docentes_nie.index.get_level_values('Nombre_Docente').str.contains(search_doc2, case=False)
        else:
            cond1 = True
        if search_school2:
            cond2 = docentes_nie.index.get_level_values('Código') == np.int32(search_school2)
        else:
            cond2 = True
        filtered_data = docentes_nie[cond1 & cond2]
    else:
        filtered_data = docentes_nie
    
    # Convertir los valores a enteros
    st.dataframe(filtered_data)

with tab7:

    # Convert starttime to datetime
    egra_invalid['starttime'] = pd.to_datetime(egra_invalid['starttime'], format='%d/%m/%Y, %H:%M:%S')
    # Create a new column for the week period
    egra_invalid['week_period'] = egra_invalid['starttime'].dt.to_period('W').apply(lambda r: f"{r.start_time.strftime('%d/%m')}-{(r.end_time - pd.Timedelta(days=1)).strftime('%d/%m')}")
    # Group by encuestador and week_period and count invalid observations
    weekly_invalids = egra_invalid.groupby(['encuestador', 'week_period'])['Invalid'].sum().unstack(fill_value=0)
    # Sort columns to have the most recent on the left
    weekly_invalids = weekly_invalids[sorted(weekly_invalids.columns, key=lambda x: pd.to_datetime(x.split('-')[0], format='%d/%m'), reverse=True)]
    # Create a column for the total invalid observations per encuestador
    total_invalids = egra_invalid.groupby('encuestador')['Invalid'].sum()
    # Merge the weekly counts with the total counts
    invalid_encuestador = pd.merge(total_invalids, weekly_invalids, on='encuestador')

    # Combine the weekly counts with the total counts
    #invalid_encuestador = weekly_invalids.assign(Total_Invalid=total_invalids)

    # Add a row for the total per week
    total_row = invalid_encuestador.sum().to_frame().T
    total_row.index = ['Total']
    invalid_encuestador = pd.concat([invalid_encuestador, total_row])
    invalid_encuestador.columns.name = 'Encuestador'
    invalid_encuestador = invalid_encuestador.sort_values(by = 'Invalid', ascending = False).rename(columns = {'Invalid': 'Invalidos'})

    st.subheader('Invalidos por Encuestador')
    st.dataframe(invalid_encuestador)

    total_doc = egra.docente_merge.value_counts().reset_index()
    inval_doc = egra_invalid.docente_merge.value_counts().reset_index()
    total_doc.rename(columns = {'count': 'Validas'}, inplace = True)
    inval_doc.rename(columns = {'count': 'Invalidas'}, inplace = True)

    inval_doc = pd.merge(total_doc, inval_doc, on = 'docente_merge', how = 'right').rename(columns = {'docente_merge': 'unique_id'}).fillna(0)
    inval_doc = pd.merge(docentes_ce[['unique_id', 'Nombre_Docente', 'Código']], inval_doc, on = 'unique_id', how= 'right')
    inval_doc['Realizadas'] = inval_doc['Validas'] + inval_doc['Invalidas']
    inval_doc = inval_doc.set_index(['unique_id', 'Código', 'Nombre_Docente' ])
    
    # Añadir buscador para filtrar por centro educativo
    st.subheader('Docentes con EGRAs Invalidas')
    search_doc3 = st.text_input('Buscar por Docente Invalido')
    search_school_inv = st.text_input('Buscar por Escuelas [usar código sin comas, ejemplo: 11135]')
    if search_doc3 or search_school_inv:
        if search_doc3:
            cond1 = inval_doc.index.get_level_values('Nombre_Docente').str.contains(search_doc, case=False)
        else:
            cond1 = True
        if search_school_inv:
            cond2 = inval_doc.index.get_level_values('Código') == np.int32(search_school)
        else:
            cond2 = True
        filtered_data_inv = inval_doc[cond1 & cond2]
    else:
        filtered_data_inv = inval_doc
    
    # Convertir los valores a enteros
    st.dataframe(filtered_data_inv)

    st.subheader('Docentes con Todas EGRAs Invalidas ')
    st.dataframe(inval_doc[inval_doc['Validas'] == 0])

    st.subheader('Invalidos por sección')
    invalid_sect = egra_invalid[['letter_invalid', 'nonwords_invalid', 'reading_invalid']]
    st.dataframe(invalid_sect.mean().reset_index().rename(columns = {'index': 'Sección', 0: 'Porcentaje'}))
