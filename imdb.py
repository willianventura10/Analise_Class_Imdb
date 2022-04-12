import re
import time
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.filterwarnings("ignore")

# Conecta no banco de dados
conn = sqlite3.connect("D:\Data_Science\Projetos\Imdb\imdb.db")

# Extrai a lista de tabelas
tabelas = pd.read_sql_query("SELECT NAME AS 'Table_Name' FROM sqlite_master WHERE type = 'table'", conn)
# Visualiza o resultado
tabelas.head(10)

# Converte o dataframe em uma lista
tabelas = tabelas["Table_Name"].values.tolist()

# Esquema de cada uma das listas
for tabela in tabelas:
    consulta = "PRAGMA TABLE_INFO({})".format(tabela)
    resultado = pd.read_sql_query(consulta, conn)
    print("Esquema da tabela:", tabela)
    display(resultado)
    print("-"*100)
    print("\n")

# Exporta CSV para trabalho no Power BI
consultax = '''
           SELECT * FROM titles
           INNER JOIN akas ON akas.title_id = titles.title_id
           INNER JOIN ratings ON ratings.title_id = titles.title_id
           WHERE premiered <= 2022 AND type = 'movie'
           ORDER BY premiered
           ''' 

resultadox = pd.read_sql_query(consultax, conn)
display(resultadox)
resultadox.to_csv("D:/Data_Science/Projetos/Imdb/imdb_csv/IMDB_BI.csv") 
    
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

# Cria vetor usando expressão regular para filtrar as strings
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

# Função para retornar os genêros
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
listas = df_genero_ratings['count']

# Drop do índice 18 (news)
df_genero_ratings = df_genero_ratings.drop(index = 18)
# Ordena o resultado
df_genero_ratings = df_genero_ratings.sort_values(by = 'rating', ascending = False)

#Exporta CSV para trabalho no Power BI
df_genero_ratings.to_csv("D:/Data_Science/Projetos/Imdb/imdb_csv/Imdb_mediana_avali_genero.csv")
