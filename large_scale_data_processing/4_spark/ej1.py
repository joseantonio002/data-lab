from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
import sys
import os, shutil, glob # Para mover el fichero parquet del directorio temporal
#
# Script para extraer información del fichero Posts.parquet de StackOverflow.
def load_posts_data(spark: SparkSession, path_posts: str) -> DataFrame:
    posts: DataFrame = (spark
        .read
        .format("parquet")
        .load(path_posts))
    
    return posts 

# a) Obtener el número de respuestas que ha recibido cada pregunta.
#    Debes obtener un DataFrame de la siguiente forma:
#   +----------+-----------+----------+
#   |QuestionId|NRespuestas|ScoreTotal|
#   +----------+-----------+----------+
#   |    4     |     13    |    120   |
#   |    6     |     26    |    300   |
#   |    9     |     33    |    400   |
#   |   11     |     15    |    150   |
#   |   13     |      8    |     80   |
def n_answers(posts: DataFrame) -> DataFrame:
    # Preguntas
    questions: DataFrame = (
        posts
        .filter(F.col("PostTypeId") == 1)
        .select(F.col("Id").alias("QuestionId"))
    )

    # Número de respuestas para preguntas que tienen al menos una respuesta
    answers_agg: DataFrame = (
        posts
        .filter(F.col("PostTypeId") == 2)
        .groupBy(F.col("ParentId").alias("QuestionId")) # Agrupar funciona igual que GROUP BY de SQL
        .agg(
            F.count(F.lit(1)).alias("NRespuestas"), # F.lit() crea una columna con unos, al sumarla contamos
            F.coalesce(F.sum(F.col("Score").cast("long")), F.lit(0)).alias("ScoreTotal"), # Nos aseguramos con coalesce por si score es null
        )
    )

    # Left join para incluir preguntas con 0 respuestas, 
    return (
        questions
        .join(answers_agg, on="QuestionId", how="left")
        .select(
            "QuestionId",
            F.coalesce(F.col("NRespuestas"), F.lit(0)).alias("NRespuestas"),
            F.coalesce(F.col("ScoreTotal"), F.lit(0)).alias("ScoreTotal"),
        )
    )
# b) A partir del fichero Posts.parquet, crear un DataFrame que contenga el Id de la pregunta, 
# el OwnerUserId y el año de creación, descartando el resto de campos del fichero.
# Ese DataFrame debe tener la siguiente forma:
#
#   +----------+------+----+ 
#   |QuestionId|UserId|Año |
#   +----------+------+----+
#   |    4     |   8  |2008|
#   |    6     |   9  |2008|
#   |    9     |   1  |2008|
#   |   11     |   1  |2008|
#   |   13     |   9  |2008|
def question_info(posts: DataFrame) -> DataFrame:
    # Primero filtramos preguntas y seleccionamos columnas que nos interesan, usando F.date_format para formatear la fecha
    return posts.filter(F.col("PostTypeId") == 1)\
    .select(F.col("Id").alias("QuestionId"), "OwnerUserId", F.date_format("CreationDate", "yyyy")\
    .alias("Año"))

# A la hora de guardar como parquet, no se guarda como un solo fichero sino como un directorio, ya que se crea
# un fichero parquet por cada partición del dataframe. Para tenerlo como un solo fichero hay que hacer DataFrame.coalesce(1)
# que devuelve un DataFrame con exactamente 1 partición, guardar, mover y renombrar el fichero parquet y borrar la carpeta temporal
def write_single_parquet(df: DataFrame, final_file_path: str) -> None:
    """
    Escribe df como UN solo fichero parquet (final_file_path), usando una carpeta temporal.
    """
    tmp_dir = final_file_path + ".__tmp__"

    # Limpia restos previos
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    if os.path.exists(final_file_path):
        # si ya existe el fichero final, lo borramos (overwrite real)
        os.remove(final_file_path)

    # 1) escribir a carpeta temporal (1 solo part)
    df.coalesce(1).write.mode("overwrite").parquet(tmp_dir)

    # 2) localizar el parquet real
    part_files = glob.glob(os.path.join(tmp_dir, "part-*.parquet"))
    if len(part_files) != 1:
        raise RuntimeError(f"Esperaba 1 part file en {tmp_dir}, pero encontré {len(part_files)}: {part_files}")

    part_file = part_files[0]

    # 3) mover/renombrar al destino final
    shutil.move(part_file, final_file_path)

    # 4) borrar carpeta temporal (incluye _SUCCESS y .crc)
    shutil.rmtree(tmp_dir)
#
# Ejecutar en local con:
# spark-submit --master 'local[*]' --driver-memory 4g e1.py Posts.parquet dfRespuestas.parquet dfPreguntas.parquet
# Ejecución en un cluster YARN:
# spark-submit --master yarn --num-executors 8 --driver-memory 4g e1.py Posts.parquet dfRespuestas.parquet dfPreguntas.parquet

def main():
    # Comprueba el número de argumentos
    # sys.argv[1] es el primer argumento, sys.argv[2] el segundo, etc.
    if len(sys.argv) != 4:
        print(f"Uso: {sys.argv[0]} Posts.parquet dfRespuestas.parquet dfPreguntas.parquet")
        exit(-1)

    spark: SparkSession = SparkSession\
        .builder\
        .appName("Ejercicio 1 de Diego")\
        .getOrCreate()

    # Cambio la verbosidad para reducir el número de
    # mensajes por pantalla
    spark.sparkContext.setLogLevel("FATAL")
    # Código del programa
    
    posts: DataFrame = load_posts_data(spark, str(sys.argv[1]))
    dfrespuestas: DataFrame = n_answers(posts)
    dfpreguntas: DataFrame = question_info(posts)

    # Un único fichero parquet con el nombre EXACTO de sys.argv[2] y sys.argv[3]
    write_single_parquet(dfrespuestas, sys.argv[2])
    write_single_parquet(dfpreguntas, sys.argv[3])



if __name__ == "__main__":
    main()
