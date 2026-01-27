from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import Column
from pyspark.sql.window import Window
import sys
import re
import os, shutil, glob
#
# Script para extraer información de un fichero parquet
def load_data(spark: SparkSession, path_parquet: str) -> DataFrame:
    df: DataFrame = (spark
        .read
        .format("parquet")
        .load(path_parquet))
    
    return df
#
# Ejecutar en local con:
# spark-submit --master 'local[*]' --driver-memory 4g e1.py Posts.parquet dfRespuestas.parquet dfPreguntas.parquet
# Ejecución en un cluster YARN:
# spark-submit --master yarn --num-executors 8 --driver-memory 4g e1.py Posts.parquet dfRespuestas.parquet dfPreguntas.parquet

def write_single_csv(df: DataFrame, final_file_path: str) -> None:
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
    df.coalesce(1).write.format("csv").mode("overwrite").option("header", True).save(tmp_dir)

    # 2) localizar el parquet real
    part_files = glob.glob(os.path.join(tmp_dir, "part-*.csv"))
    if len(part_files) != 1:
        raise RuntimeError(f"Esperaba 1 part file en {tmp_dir}, pero encontré {len(part_files)}: {part_files}")

    part_file = part_files[0]

    # 3) mover/renombrar al destino final
    shutil.move(part_file, final_file_path)

    # 4) borrar carpeta temporal (incluye _SUCCESS y .crc)
    shutil.rmtree(tmp_dir)



def main():
    # Comprueba el número de argumentos
    # sys.argv[1] es el primer argumento, sys.argv[2] el segundo, etc.
    if len(sys.argv) != 6:
        print(f"Uso: {sys.argv[0]} dfRespuestas.parquet dfPreguntas.parquet Posts.parquet lista,tags,separados,coma out.csv")
        exit(-1)

    spark: SparkSession = SparkSession\
        .builder\
        .appName("Ejercicio 1 de Diego")\
        .getOrCreate()
 
    tags_to_study: list[str] = [t.strip().lower() for t in sys.argv[4].split(",") if t.strip()]
    # Construimos una columna de tipo array que contiene los tags como literales constantes para luego poder hacer F.array_intersect con los tags de esa columna
    # F.lit(t) convierte cada string Python en un literal de Spark (una Column constante)
    # El * (splat) “desempaqueta” esa lista para pasarla como argumentos posicionales a F.array(...)
    study_arr: Column = F.array(*[F.lit(t) for t in tags_to_study])

    # Cambio la verbosidad para reducir el número de
    # mensajes por pantalla
    spark.sparkContext.setLogLevel("FATAL")
    
    posts: DataFrame = load_data(spark, sys.argv[3])
    dfPreguntas: DataFrame = load_data(spark, sys.argv[2])
    dfRespuestas: DataFrame = load_data(spark, sys.argv[1])

    # Creamos una nueva columna con los tags como un array de strings usando F.split para luego poder hacer F.array_intersect
    posts2 = posts.filter(F.col("PostTypeId") == 1).withColumn(
        "TagsArr",
        F.split(
            F.regexp_replace(F.col("Tags"), r"^<|>$", ""),   # quita el primer "<" y el último ">", cadena de texto que vamos a dividir
            r"><"                                           # separa por "><", caracter por el que vamos a dividir
        )
    )

    # Usando F.array_intersect nos quedamos con las preguntas que tengan al menos un tag en tags_to_study
    posts_filtrado: DataFrame = posts2.filter(F.size(F.array_intersect(F.col("TagsArr"), study_arr)) > 0).select("Id", "TagsArr")

    # Unimos los dataframes del ejercicio 1 y nos quedamos con las columnas que nos interesan, filtramos de posts los que tengan
    # tags que vamos a estudiar uniendo con posts_filtrado de manera inner y de paso les dejamos la columna TagsArr
    # para en el siguiente paso "explotar" por tags
    dfBase = (
        dfPreguntas
        .join(dfRespuestas, on="QuestionId", how="inner")
        .select("QuestionId", "Año", "NRespuestas")
        .join(
            posts_filtrado.select(F.col("Id").alias("PostId"), "TagsArr"),
            on=(F.col("QuestionId") == F.col("PostId")),
            how="inner"
        )
        .drop("PostId")
    )

    # Construimos un DataFrame “normalizado” a nivel de tag, nos quedamos de todos los tags de la pregunta
    # con los que estamos estudiando (StudyTags) aprovechando de nuevo F.array_intersect y eliminando duplicados
    # con arrayDistinct
    # “Explotamos” (convertir un array en varias filas) StudyTags para tener una fila por (Tag, Año, QuestionId)
    dfPorTag = (
        dfBase
        .withColumn("TagsArr", F.transform("TagsArr", lambda x: F.lower(x)))
        # solo los tags estudiados (y sin duplicados)
        .withColumn(
            "StudyTags",
            F.array_distinct(F.array_intersect(F.col("TagsArr"), study_arr))
        )
        # una fila por tag estudiado
        .withColumn("Tag", F.explode("StudyTags"))
        .select("Tag", "Año", "QuestionId", "NRespuestas")
    )

    # Definimos la ventana para el ranking, igual que en SQL PARTITION BY y ORDER BY
    w = Window.partitionBy("Tag", "Año").orderBy(F.col("NRespuestas").desc(), F.col("QuestionId").asc())

    # Calculamos el ranking usando row_number() sobre la ventana que definimos
    dfFinal = (
        dfPorTag
        .withColumn("Rango", F.row_number().over(w))   # 1,2,3,... sin empates
        # alternativa si quieres empates: F.dense_rank().over(w)
    ).orderBy(
        F.col("Tag").asc(),
        F.col("Año").asc(),
        F.col("NRespuestas").desc(),
    )

    write_single_csv(dfFinal, sys.argv[5])



if __name__ == "__main__":
    main()
