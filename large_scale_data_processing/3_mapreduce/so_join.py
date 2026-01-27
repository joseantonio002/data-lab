from mrjob.job import MRJob
from mrjob.protocol import TextProtocol
from collections.abc import Iterable, Iterator
import csv


class MRJoinQuestionsWithUser(MRJob):
    # Queremos: 495829\t(39,Daniel)
    OUTPUT_PROTOCOL = TextProtocol

    # Índices Posts.csv
    POST_ID = 0
    POST_OWNER = 15
    POST_TYPE = 17

    # Índices Users.csv
    USER_ID = 0
    USER_DISPLAY = 4
    USER_REP = 8

    def mapper(self, _: str | None, line: str) -> Iterator[tuple[int, tuple[str, str, str]]]:
        # Formato esperado: "P|<csv...>" o "U|<csv...>"
        if len(line) < 3 or line[1] != "|":
            return

        rec_type = line[0] # Si es Post P o User u
        raw = line[2:] # Datos de la línea (Nos saltamos P|)

        # Saltar cabeceras (después del prefijo)
        if raw.startswith("Id"):
            return

        try:
            row = next(csv.reader([raw]))

            if rec_type == "P":
                # Solo preguntas
                if int(row[self.POST_TYPE]) != 1:
                    return

                owner_raw = row[self.POST_OWNER]
                if not owner_raw:
                    return
                owner_id = int(owner_raw)

                qid = row[self.POST_ID]
                # Emitimos: key=OwnerUserId, value=("P", question_id, "")
                yield owner_id, ("P", qid, "")

            elif rec_type == "U":
                uid_raw = row[self.USER_ID]
                if not uid_raw:
                    return
                uid = int(uid_raw)

                rep = row[self.USER_REP]
                name = row[self.USER_DISPLAY]
                # Emitimos: key=UserId, value=("U", rep, name)
                yield uid, ("U", rep, name)

        except Exception:
            return

    def reducer(self, owner_id: int, values: Iterable[tuple[str, str, str]]
                ) -> Iterator[tuple[str, str]]:
        rep = None
        name = None
        question_ids: list[str] = []

        # Obtenemos las preguntas (tag == "P") e información de la reputación (tag == "U")
        for tag, a, b in values:
            if tag == "U":
                rep, name = a, b
            elif tag == "P":
                question_ids.append(a)

        # Si no hay usuario
        if rep is None or name is None:
            return

        for qid in question_ids:
            yield str(qid), f"({rep},{name})"


if __name__ == "__main__":
    MRJoinQuestionsWithUser.run()
