#! /usr/bin/env python3
import shutil
import sys

from pyarrow.fs import FileInfo, FileSystem, FileType


def copy_half_file(uri1: str, uri2: str) -> None:
    """Copia la segunda mitad (por bytes) de un archivo desde uri1 a uri2.

    Args:
        uri1 (str): URI del archivo de origen (por ejemplo: hdfs:///... o file:///...).
        uri2 (str): URI del archivo de destino.
    """
    # 1) Resolver qué sistema de archivos y qué ruta interna corresponde a cada URI
    fs1, path1 = FileSystem.from_uri(uri1)
    fs2, path2 = FileSystem.from_uri(uri2)

    # 2) Obtener información del archivo origen (tamaño, tipo, etc.)
    f_info: FileInfo = fs1.get_file_info(path1)

    # 3) Comprobaciones básicas
    if f_info.type == FileType.NotFound:
        raise FileNotFoundError(f"No existe el archivo origen: {uri1}")
    if f_info.type != FileType.File:
        raise IsADirectoryError(f"El origen no es un archivo regular: {uri1}")

    # 4) Calcular la mitad del archivo (en bytes)
    half = f_info.size // 2

    # 5) Abrir origen y destino
    # - open_input_file: lectura tipo "archivo" (permite seek)
    # - open_output_stream: escritura en el destino (stream de bytes)
    with fs1.open_input_file(path1) as instream, fs2.open_output_stream(path2) as outstream:
        # 6) Mover el puntero del archivo de entrada a la mitad
        instream.seek(half)

        # 7) Copiar desde esa posición hasta el final al archivo destino
        #    copyfileobj copia de un "file-like object" a otro, por bloques.
        shutil.copyfileobj(instream, outstream)


if __name__ == "__main__":
    # Si no se proporcionan dos argumentos, se muestra un mensaje de error
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <uri_origen> <uri_destino>", file=sys.stderr)
        print("Ejemplos:", file=sys.stderr)
        print(f"  {sys.argv[0]} hdfs:///user/luser/a.txt file:///home/luser/mitad.txt", file=sys.stderr)
        print(f"  {sys.argv[0]} file:///home/luser/a.txt hdfs:///user/luser/mitad.txt", file=sys.stderr)
        sys.exit(1)

    copy_half_file(sys.argv[1], sys.argv[2])
