import re
import time
import sqlite3
import pycountry
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import cm
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.filterwarnings("ignore")
sns.set_theme(style = "whitegrid")

# Conecta no banco de dados
conn = sqlite3.connect("D:\Data_Science\Projetos\Imdb\imdb.db")

# Extrai a lista de tabelas
tabelas = pd.read_sql_query("SELECT NAME AS 'Table_Name' FROM sqlite_master WHERE type = 'table'", conn)
# Visualiza o resultado
tabelas.head(10)

# Vamos converter o dataframe em uma lista
tabelas = tabelas["Table_Name"].values.tolist()

# Vamos percorrer a lista de tabelas no banco de dados e extrair o esquema de cada uma
for tabela in tabelas:
    consulta = "PRAGMA TABLE_INFO({})".format(tabela)
    resultado = pd.read_sql_query(consulta, conn)
    print("Esquema da tabela:", tabela)
    display(resultado)
    print("-"*100)
    print("\n")
    
    
    
# QUAL O NÚMERO DE TÍTULOS POR GÊNERO

# Cria a consulta SQL
consulta2 = '''SELECT genres, COUNT(*) FROM titles WHERE type = 'movie' GROUP BY genres''' 

# Resultado
resultado2 = pd.read_sql_query(consulta2, conn)

# Converte as strings para minúsculo
resultado2['genres'] = resultado2['genres'].str.lower().values
display(resultado2)

# Remove valores NA (ausentes)
temp = resultado2['genres'].dropna()

# Visualiza o resultado
display(temp)

# Será criado um vetor usando expressão regular para filtrar as strings
# https://docs.python.org/3.8/library/re.html
padrao = '(?u)\\b[\\w-]+\\b'

# https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html
vetor = CountVectorizer(token_pattern = padrao, analyzer = 'word').fit(temp)
type(vetor)

# Aplica a vetorização ao dataset sem valores NA
bag_generos = vetor.transform(temp)

type(bag_generos)

# Retorna gêneros únicos
generos_unicos =  vetor.get_feature_names()
# Cria o dataframe de gêneros
generos = pd.DataFrame(bag_generos.todense(), columns = generos_unicos, index = temp.index)
# Visualiza
generos.info()

# Drop da coluna n
generos = generos.drop(columns = 'n', axis = 0)
# Visualiza
generos.info()

# Calcula o percentual
generos_percentual = 100 * pd.Series(generos.sum()).sort_values(ascending = False) / generos.shape[0]
# Visualiza
generos_percentual.head(10)

# Plot
plt.figure(figsize = (16,8))
sns.barplot(x = generos_percentual.values, y = generos_percentual.index, orient = "h", palette = "terrain")
plt.ylabel('Gênero')             
plt.xlabel("\nPercentual de Filmes (%)")
plt.title('\nNúmero (Percentual) de Títulos Por Gênero\n')
plt.show()


# MEDIANA DE AVALIAÇÃO DOS FILMES POR GÊNERO
# Consulta SQL
consulta3 = '''
            SELECT rating, genres FROM 
            ratings JOIN titles ON ratings.title_id = titles.title_id 
            WHERE premiered <= 2022 AND type = 'movie'
            ''' 
# Resultado
resultado3 = pd.read_sql_query(consulta3, conn)
# Visualiza
display(resultado3)

# Vamos criar uma função para retornar os genêros
def retorna_generos(df):
    df['genres'] = df['genres'].str.lower().values
    temp = df['genres'].dropna()
    vetor = CountVectorizer(token_pattern = '(?u)\\b[\\w-]+\\b', analyzer = 'word').fit(temp)
    generos_unicos =  vetor.get_feature_names()
    generos_unicos = [genre for genre in generos_unicos if len(genre) > 1]
    return generos_unicos

# Aplica a função
generos_unicos = retorna_generos(resultado3)
# Visualiza
generos_unicos

# Cria listas vazias
genero_counts = []
genero_ratings = []

# Loop
for item in generos_unicos:
    
    # Retorna a contagem de filmes por gênero
    consulta = 'SELECT COUNT(rating) FROM ratings JOIN titles ON ratings.title_id=titles.title_id WHERE genres LIKE '+ '\''+'%'+item+'%'+'\' AND type=\'movie\''
    resultado = pd.read_sql_query(consulta, conn)
    genero_counts.append(resultado.values[0][0])
  
     # Retorna a avaliação de filmes por gênero
    consulta = 'SELECT rating FROM ratings JOIN titles ON ratings.title_id=titles.title_id WHERE genres LIKE '+ '\''+'%'+item+'%'+'\' AND type=\'movie\''
    resultado = pd.read_sql_query(consulta, conn)
    genero_ratings.append(np.median(resultado['rating']))
    
# Prepara o dataframe final
df_genero_ratings = pd.DataFrame()
df_genero_ratings['genres'] = generos_unicos
df_genero_ratings['count'] = genero_counts
df_genero_ratings['rating'] = genero_ratings

# Visualiza
df_genero_ratings.head(20)

# Drop do índice 18 (news)
# Não queremos essa informação como gênero
df_genero_ratings = df_genero_ratings.drop(index = 18)
# Ordena o resultado
df_genero_ratings = df_genero_ratings.sort_values(by = 'rating', ascending = False)
# Plot

# Figura
plt.figure(figsize = (16,10))

# Barplot
sns.barplot(y = df_genero_ratings.genres, x = df_genero_ratings.rating, orient = "h")

# Textos do gráfico
for i in range(len(df_genero_ratings.index)):
    
    plt.text(4.0, 
             i + 0.25, 
             str(df_genero_ratings['count'][df_genero_ratings.index[i]]) + " filmes")
    
    plt.text(df_genero_ratings.rating[df_genero_ratings.index[i]],
             i + 0.25,
             round(df_genero_ratings["rating"][df_genero_ratings.index[i]],2))

plt.ylabel('Gênero')             
plt.xlabel('Mediana da Avaliação')
plt.title('\nMediana de Avaliação Por Gênero\n')
plt.show()

#QUAL A MEDIANA DE AVALIAÇÃO DOS FILMES EM RELAÇÃO AO ANO DE ESTRÉIA?

# Consulta SQL
consulta4 = '''
            SELECT rating AS Rating, premiered FROM 
            ratings JOIN titles ON ratings.title_id = titles.title_id 
            WHERE premiered <= 2022 AND type = 'movie'
            ORDER BY premiered
            ''' 
# Resultado
resultado4 = pd.read_sql_query(consulta4, conn)
display(resultado4)

# Calcula a mediana ao longo do tempo (anos)
ratings = []
for year in set(resultado4['premiered']):
    ratings.append(np.median(resultado4[resultado4['premiered'] == year]['Rating']))
type(ratings)

ratings[1:10]

# Lista de anos
anos = list(set(resultado4['premiered']))
anos[1:10]

# Plot
plt.figure(figsize = (16,8))
plt.plot(anos, ratings)
plt.xlabel('\nAno')
plt.ylabel('Mediana de Avaliação')
plt.title('\nMediana de Avaliação dos Filmes Em Relação ao Ano de Estréia\n')
plt.show()

#QUAL O NÚMERO DE FILMES AVALIADOS POR GÊNERO EM RELAÇÃO AO ANO DE ESTRÉIA?

# Consulta SQL
consulta5 = '''SELECT genres FROM titles ''' 
# Resultado
resultado5 = pd.read_sql_query(consulta5, conn)
display(resultado5)

# Retorna gêneros únicos
generos_unicos = retorna_generos(resultado5)

# Visualiza o resultado
generos_unicos

# Agora fazemos a contagem
genero_count = []
for item in generos_unicos:
    consulta = 'SELECT COUNT(*) COUNT FROM  titles  WHERE genres LIKE '+ '\''+'%'+item+'%'+'\' AND type=\'movie\' AND premiered <= 2022'
    resultado = pd.read_sql_query(consulta, conn)
    genero_count.append(resultado['COUNT'].values[0])
    
# Prepara o dataframe
df_genero_count = pd.DataFrame()
df_genero_count['genre'] = generos_unicos
df_genero_count['Count'] = genero_count

# Calcula os top 5
df_genero_count = df_genero_count[df_genero_count['genre'] != '\n']
df_genero_count = df_genero_count.sort_values(by = 'Count', ascending = False)
top_generos = df_genero_count.head()['genre'].values

# Plot

# Figura
plt.figure(figsize = (16,8))

# Loop e Plot
for item in top_generos:
    consulta = 'SELECT COUNT(*) Number_of_movies, premiered Year FROM  titles  WHERE genres LIKE '+ '\''+'%'+item+'%'+'\' AND type=\'movie\' AND Year <=2022 GROUP BY Year'
    resultado = pd.read_sql_query(consulta, conn)
    plt.plot(resultado['Year'], resultado['Number_of_movies'])

plt.xlabel('\nAno')
plt.ylabel('Número de Filmes Avaliados')
plt.title('\nNúmero de Filmes Avaliados Por Gênero Em Relação ao Ano de Estréia\n')
plt.legend(labels = top_generos)
plt.show()

# QUAL O FILME COM MAIOR TEMPO DE DURAÇÃO? 

# Consulta SQL
consulta6 = '''SELECT runtime_minutes Runtime FROM titles WHERE type = 'movie' AND Runtime != 'NaN' '''
# Resultado
resultado6 = pd.read_sql_query(consulta6, conn)
display(resultado6)

# cálculo dos percentis
for i in range(101): 
    perc = round(np.percentile(resultado6['Runtime'].values, i), 2)
    print('{} percentil da duração (runtime) é: {}'.format(i, perc))

# Refazendo a consulta e retornando o filme com maior duração
consulta6 = '''
            SELECT runtime_minutes Runtime, primary_title
            FROM titles 
            WHERE type = 'movie' AND Runtime != 'NaN'
            ORDER BY Runtime DESC
            LIMIT 1
            ''' 
resultado6 = pd.read_sql_query(consulta6, conn)
resultado6 