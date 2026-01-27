from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import Column
from pyspark.sql.window import Window
import sys
import re
import os, shutil, glob # Para mover el fichero parquet del directorio temporal
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
    if len(sys.argv) != 5:
        print(f"Uso: {sys.argv[0]} dfPreguntas.parquet Posts.parquet Users.parquet out.csv")
        exit(-1)

    spark: SparkSession = SparkSession\
        .builder\
        .appName("Ejercicio 1 de Diego")\
        .getOrCreate()

    # Cambio la verbosidad para reducir el número de
    # mensajes por pantalla
    spark.sparkContext.setLogLevel("FATAL")
    
    posts: DataFrame = load_data(spark, sys.argv[2])
    dfPreguntas: DataFrame = load_data(spark, sys.argv[1])
    users: DataFrame = load_data(spark, sys.argv[3])

    # Añadimos los tags a dfPreguntas
    dfPreguntasTags: DataFrame = (dfPreguntas.join(users, on=(F.col("Id") == F.col("OwnerUserId")), how="inner")
                                  .select("DisplayName", "QuestionId", "Año").
                                  join(posts, on=(F.col("Id") == F.col("QuestionId")), how="inner").
                                  select("DisplayName", "Tags", "Año").withColumnRenamed('DisplayName', 'Usuario'))

    # Misma técnica que en el ejercicio anterior (ej3.py) para tener una fila por cada tag
    # En este caso es mas sencillo porque no nos hace falta filtrar tags
    dfPorTag = (
        dfPreguntasTags
        # "<java><python>" -> ["java","python"]
        .withColumn(
            "TagsArr",
            F.split(F.regexp_replace(F.col("Tags"), r"^<|>$", ""), r"><")
        )
        # una fila por tag estudiado
        .withColumn("Tag", F.explode("TagsArr"))
        .select("Usuario", "Tag", "Año")
    )

    # Asegurarse de ordenar por año ascendiente
    w = Window.partitionBy("Usuario", "Tag").orderBy(F.col("Año").asc())

    # Para calcular la diferencia usamos la función lag(), que devuelve el valor de la fila anterior en la ventana
    # Si es el primer año, Dif lo ponemos a 0 con coalesce
    df = (dfPorTag
        .groupBy("Usuario", "Tag", "Año")
        .agg(F.count("*").alias("NPreguntas"))
        .withColumn("Prev", F.lag("NPreguntas", 1).over(w))
        .withColumn("Dif", F.coalesce(F.col("NPreguntas") - F.col("Prev"), F.lit(0)))
        .drop("Prev")
        .sort("Usuario", "Tag", F.col("Año").asc())
    )

    write_single_csv(df, sys.argv[4])


if __name__ == "__main__":
    main()
