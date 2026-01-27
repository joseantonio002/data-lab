from mrjob.job import MRJob
from mrjob.protocol import TextProtocol
from collections.abc import Iterable, Iterator
import csv
import re
from itertools import combinations


class MRTagConcurrence(MRJob):
    # Para salida tipo: "python,pandas\t89"
    OUTPUT_PROTOCOL = TextProtocol

    def mapper(self, _: str | None, line: str) -> Iterator[tuple[str, int]]:
        if line.startswith("Id"):
            return
        try:
            row = next(csv.reader([line]))
            # Solo preguntas
            if int(row[17]) != 1:
                return
            tags_field = row[19]
            if not tags_field:
                return
            tags = re.findall(r"<([^>]+)>", tags_field)
            if len(tags) < 2: # Nos aseguramos que tiene al menos dos tags
                return

            # Por seguridad: quitar duplicados y ordenar para consistencia
            tags = sorted(set(tags))

            # Generar pares únicos (combinaciones)
            for t1, t2 in combinations(tags, 2):
                yield f"{t1},{t2}", 1

        except Exception:
            # Saltar líneas mal formadas
            return

    def combiner(self, key: str, values: Iterable[int]) -> Iterator[tuple[str, int]]:
        yield key, sum(values)

    def reducer(self, key: str, values: Iterable[int]) -> Iterator[tuple[str, str]]:
        # TextProtocol requiere strings en salida
        yield key, str(sum(values))


if __name__ == "__main__":
    MRTagConcurrence.run()
