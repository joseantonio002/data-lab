from mrjob.job import MRJob
from mrjob.step import MRStep
from collections.abc import Iterable, Iterator
import csv
import heapq

class MRCountAnswersTopK(MRJob):

    def configure_args(self):
        super().configure_args()
        self.add_passthru_arg("--top-k", type=int, default=20, help="Número de elementos a devolver")
        self.add_passthru_arg("--num-buckets", type=int, default=100, help="Número de buckets")

    def steps(self):
        return [
            MRStep(mapper=self.mapper_count,
                   combiner=self.combiner_count,
                   reducer=self.reducer_count),
            MRStep(mapper=self.mapper_bucketize,
                   reducer=self.reducer_topk_per_bucket),
            MRStep(reducer=self.reducer_topk_global),
        ]

    # Paso 1: contar respuestas por ParentId
    def mapper_count(self, _: str | None, line: str) -> Iterator[tuple[int, int]]:
        if line.startswith("Id"):
            return
        try:
            row = next(csv.reader([line]))
            if int(row[17]) != 2:
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
        yield parent_id, sum(values)

    # Paso 2: repartir en buckets y top-k local
    def mapper_bucketize(self, parent_id: int, count: int) -> Iterator[tuple[int, tuple[int, int]]]:
        # Bucket estable a partir del parent_id
        b = parent_id % self.options.num_buckets
        # Guardamos (count, parent_id) para comparar por count
        yield b, (count, parent_id)

    def reducer_topk_per_bucket(self, bucket_id: int, items: Iterable[tuple[int, int]]
                                ) -> Iterator[tuple[None, tuple[int, int]]]:
        k = self.options.top_k
        heap: list[tuple[int, int]] = []  # min-heap de (count, parent_id)

        for count, parent_id in items:
            if len(heap) < k:
                heapq.heappush(heap, (count, parent_id))
            else:
                # si el nuevo es mayor que el mínimo del heap, reemplaza
                if (count, parent_id) > heap[0]:
                    heapq.heapreplace(heap, (count, parent_id))

        # Emitimos top-k local hacia un único reducer final
        for count, parent_id in heap:
            yield None, (count, parent_id)

    # Paso 3: top-k global
    def reducer_topk_global(self, _: None, pairs: Iterable[tuple[int, int]]
                            ) -> Iterator[tuple[int, int]]:
        k = self.options.top_k
        heap: list[tuple[int, int]] = []

        for count, parent_id in pairs:
            if len(heap) < k:
                heapq.heappush(heap, (count, parent_id))
            else:
                if (count, parent_id) > heap[0]:
                    heapq.heapreplace(heap, (count, parent_id))

        # Salida final ordenada desc por count
        for count, parent_id in sorted(heap, reverse=True):
            yield parent_id, count

if __name__ == "__main__":
    MRCountAnswersTopK.run()
