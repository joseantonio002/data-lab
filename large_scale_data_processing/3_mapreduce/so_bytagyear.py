from mrjob.job import MRJob
from mrjob.protocol import TextProtocol
from collections.abc import Iterable, Iterator
import csv
import re

class MRQuestionsByTagYear(MRJob):
    OUTPUT_PROTOCOL = TextProtocol  # exige key y value como str

    def mapper(self, _: str | None, line: str) -> Iterator[tuple[str, int]]:
        if line.startswith("Id"):
            return
        try:
            row = next(csv.reader([line]))

            # Solo preguntas
            if int(row[17]) != 1:
                return

            creation_date = row[8]
            year_str = creation_date[:4]
            if not year_str.isdigit():
                return
            year = int(year_str)

            tags_field = row[19]
            if not tags_field:
                return
            # Filtramos todos los tags de la pregunta, y para cada uno y el año actual añadimos uno
            tags = re.findall(r"<([^>]+)>", tags_field)
            for tag in tags:
                yield f"({year},{tag})", 1

        except Exception:
            return

    def combiner(self, key: str, values: Iterable[int]) -> Iterator[tuple[str, int]]:
        yield key, sum(values)

    def reducer(self, key: str, values: Iterable[int]) -> Iterator[tuple[str, str]]:
        total = sum(values)
        yield key, str(total)   # convertir a str para TextProtocol

if __name__ == "__main__":
    MRQuestionsByTagYear.run()
