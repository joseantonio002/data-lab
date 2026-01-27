from mrjob.job import MRJob
from mrjob.step import MRStep
from collections.abc import Iterable, Iterator
import csv

class MRCountAnswersOrdered(MRJob):

    def steps(self):
        return [
            MRStep(mapper=self.mapper_count,
                   combiner=self.combiner_count,
                   reducer=self.reducer_count),
            MRStep(reducer=self.reducer_sort)
        ]

    # Paso 1: contar respuestas por pregunta (ParentId)
    def mapper_count(self, _: str | None, line: str) -> Iterator[tuple[int, int]]:
        if line.startswith("Id"):
            return
        try:
            row = next(csv.reader([line]))
            if int(row[17]) != 2:   # PostTypeId == 2 => Answer
                return
            parent_raw = row[16]
            if not parent_raw:
                return
            yield int(parent_raw), 1
        except Exception:
            return

    def combiner_count(self, parent_id: int, values: Iterable[int]) -> Iterator[tuple[int, int]]:
        yield parent_id, sum(values)

    def reducer_count(self, parent_id: int, values: Iterable[int]) -> Iterator[tuple[int, int]]:
        # Devolvemos pares clave-valor con la misma clave para que vayan todos al mismo reducer
        yield None, (sum(values), parent_id)

    # Paso 2: ordenar por número de respuestas
    def reducer_sort(self, _: None, pairs: int) -> Iterator[tuple[None, tuple[int, int]]]:
        for count, word in sorted(pairs, key=lambda x: (-x[0], x[1])):  
            yield word, count  


if __name__ == "__main__":
    MRCountAnswersOrdered.run()
