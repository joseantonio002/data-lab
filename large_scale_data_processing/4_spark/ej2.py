from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
import sys
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
    if len(sys.argv) != 4:
        print(f"Uso: {sys.argv[0]} Ruta_Posts.parquet Ruta_Users.parquet out.csv")
        exit(-1)

    spark: SparkSession = SparkSession\
        .builder\
        .appName("Ejercicio 1 de Diego")\
        .getOrCreate()

    # Cambio la verbosidad para reducir el número de
    # mensajes por pantalla
    spark.sparkContext.setLogLevel("FATAL")
    
    posts = load_data(spark, str(sys.argv[1]))
    users = load_data(spark, str(sys.argv[2]))

    # Como tenemos que calcular agregados sobre campos de preguntas, primero filtramos solo preguntas, 
    # unimos con user para tener el nombre de usuario y nos quedamos con las
    # columnas que nos interesan para luego hacer la agrupación
    d: DataFrame = posts.filter(F.col("PostTypeId") == 1).alias("p").\
        join(users.alias("u"), F.col("p.OwnerUserId") == F.col("u.Id"), 'inner').\
        select("p.AnswerCount", "p.CommentCount", "u.DisplayName", F.date_format("p.CreationDate", "yyyy").alias("Año"))
    
    # Agrupamos y calculamos las agregaciones que nos interesan
    d = d.groupBy(F.col("u.DisplayName").alias("Usuario"), "Año").agg(F.count("*").alias("NumPreguntas"), F.sum("p.AnswerCount").alias("TotalRespuestas"),\
                                          F.sum("p.CommentCount").alias("TotalComentarios"), F.avg("p.AnswerCount").alias("MediaRespuestas"),\
                                            F.max("p.AnswerCount").alias("MaxRespuestas"))
    
    # Redondeamos MediaRespuestas
    d = d.withColumn("MediaRespuestas", F.round("MediaRespuestas", 2) )

    write_single_csv(d, sys.argv[3])


if __name__ == "__main__":
    main()
