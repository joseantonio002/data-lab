from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import JSONProtocol, TextProtocol
from collections.abc import Iterable, Iterator
import csv
import re


TAG_RE = re.compile(r"<([^>]+)>")


class MRTechnologyEvolution(MRJob):
    # Protocolo usado entre los MRStep
    INTERNAL_PROTOCOL = JSONProtocol
    # Salida final tabulada
    OUTPUT_PROTOCOL = TextProtocol

    def steps(self):
        return [
            # Paso 1a (conceptual paso 1): join preguntas-respuestas por Id/ParentId y emitir actividad ponderada por (tag, yyyy-mm)
            MRStep(mapper=self.mapper_join_inputs,
                   reducer=self.reducer_join_emit_activity),
            # Paso 1b: agregar actividad total por (tag, yyyy-mm)
            MRStep(combiner=self.combiner_sum_activity,
                   reducer=self.reducer_sum_activity),
            # Paso 2: deltas mes a mes por tag
            MRStep(mapper=self.mapper_to_tag,
                   reducer=self.reducer_monthly_deltas),
            # Paso 3: promedio últimos 6 deltas y clasificación
            MRStep(mapper=self.mapper_pass_deltas,
                   reducer=self.reducer_classify_trend,
                   jobconf={"mapreduce.job.reduces": "1"}),
        ]

    
    # Paso 1a: join interno
    def mapper_join_inputs(self, _: str | None, line: str) -> Iterator[tuple[int, tuple]]:
        # Índices:
        # Id:0, CreationDate:8, Tags:19, ParentId:16, PostTypeId:17
        if line.startswith("Id"):
            return

        try:
            row = next(csv.reader([line]))
            post_type = int(row[17])
            creation = row[8]
            if len(creation) < 7:
                return
            ym = creation[:7]  # "YYYY-MM"

            if post_type == 1:
                # Pregunta: key = question_id
                qid_raw = row[0]
                if not qid_raw:
                    return
                qid = int(qid_raw)
                tags_field = row[19] or ""
                yield qid, ("Q", ym, tags_field)

            elif post_type == 2:
                # Respuesta: key = parent_id (id de la pregunta)
                parent_raw = row[16]
                if not parent_raw:
                    return
                parent_id = int(parent_raw)
                yield parent_id, ("A", ym)

        except Exception:
            return

    def reducer_join_emit_activity(self, qid: int, records: Iterable[tuple]) -> Iterator[tuple[tuple[str, str], float]]:
        # Queremos:
        # - actividad preguntas: 1.0 por tag en mes de la pregunta
        # - actividad respuestas: 0.5 por tag en mes de la respuesta (tags vienen de la pregunta)
        q_month = None
        tags_field = None
        answer_months: list[str] = []

        for rec in records:
            if not rec:
                continue
            if rec[0] == "Q":
                # ("Q", ym, tags_field)
                q_month = rec[1]
                tags_field = rec[2]
            elif rec[0] == "A":
                # ("A", ym)
                answer_months.append(rec[1])

        if not tags_field:
            return

        tags = TAG_RE.findall(tags_field)
        if not tags:
            return

        # dedupe por seguridad y orden estable
        tags = sorted(set(tags))

        # agregación local pequeña para reducir emisiones
        acc: dict[tuple[str, str], float] = {}

        # pregunta cuenta 1.0 en su mes (si hay)
        if q_month is not None:
            for t in tags:
                k = (t, q_month)
                acc[k] = acc.get(k, 0.0) + 1.0

        # respuestas cuentan 0.5 en el mes de cada respuesta
        for am in answer_months:
            for t in tags:
                k = (t, am)
                acc[k] = acc.get(k, 0.0) + 0.5

        for k, v in acc.items():
            yield k, v

    # Paso 1b: sumar actividad
    def combiner_sum_activity(self, key: tuple[str, str], values: Iterable[float]) -> Iterator[tuple[tuple[str, str], float]]:
        yield key, sum(values)

    def reducer_sum_activity(self, key: tuple[str, str], values: Iterable[float]) -> Iterator[tuple[tuple[str, str], float]]:
        yield key, sum(values)

    # Paso 2: deltas por tag
    def mapper_to_tag(self, key: tuple[str, str], activity: float) -> Iterator[tuple[str, tuple[str, float]]]:
        tag, ym = key
        yield tag, (ym, activity)

    def reducer_monthly_deltas(self, tag: str, ym_activity: Iterable[tuple[str, float]]
                             ) -> Iterator[tuple[str, tuple[str, float]]]:
        data = list(ym_activity)
        # "YYYY-MM" ordena bien lexicográficamente
        data.sort(key=lambda x: x[0])

        prev_ym = None
        prev_act = None

        for ym, act in data:
            if prev_ym is not None:
                delta = act - (prev_act or 0.0)
                # salida temporal: (tag, ym) -> delta (lo emitimos como tag -> (ym, delta))
                yield tag, (ym, delta)
            prev_ym = ym
            prev_act = act

    # Paso 3: promedio últimos 6 deltas y clasificación
    def mapper_pass_deltas(self, tag: str, ym_delta: tuple[str, float]) -> Iterator[tuple[str, tuple[str, float]]]:
        yield tag, ym_delta

    def reducer_classify_trend(self, tag: str, ym_deltas: Iterable[tuple[str, float]]
                              ) -> Iterator[tuple[str, str]]:
        data = list(ym_deltas)
        if not data:
            return

        data.sort(key=lambda x: x[0])  # por mes
        last = data[-6:]               # últimos 6 deltas (o menos)

        n = len(last)
        avg = sum(d for _, d in last) / n if n else 0.0

        if avg > 0:
            trend = "CRECIMIENTO"
        elif avg < 0:
            trend = "DECLIVE"
        else:
            trend = "ESTABLE"

        # 1 decimal, signo sólo en negativos
        avg_str = f"{avg:.1f}"

        # salida final tabulada: Tag \t tendencia \t promedio_delta \t meses_considerados
        yield tag, f"{trend}\t{avg_str}\t{n}"


if __name__ == "__main__":
    MRTechnologyEvolution.run()
