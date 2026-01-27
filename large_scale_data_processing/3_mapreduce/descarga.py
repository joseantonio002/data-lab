import os
import tarfile
import urllib.request

# URLs de descarga
file: str = "es.stackoverflow.csv.tar.gz"
URL: str = f"https://github.com/dsevilla/bd2-data/releases/download/parquet-files-25-26/{file}"

# Descargar el fichero tar.gz
urllib.request.urlretrieve(URL, file)
assert os.path.isfile(file), f"Error: {file} no se ha descargado correctamente."

# Extraer archivos
with tarfile.open(file, "r:gz") as tar:
    for member in tar.getmembers():
        if member.name.endswith(("Posts.csv", "Users.csv")):
            tar.extract(member)
