from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

HI = time(8, 0)
HF = time(18, 0)

FF = {(1, 1), (1, 22), (5, 1), (6, 21), (8, 6), (9, 14), (11, 2), (12, 25)}

UMBRAL_RIESGO = 0.8

_cache: dict[date, bool] = {}


@dataclass(frozen=True)
class EstadoSla:
    horas_transcurridas: float
    horas_limite: int
    horas_restantes: float
    porcentaje_consumido: float
    vencida: bool
    en_riesgo: bool

    @property
    def etiqueta(self) -> str:
        if self.vencida:
            return "Vencida"
        if self.en_riesgo:
            return "En riesgo"
        return "Dentro de SLA"


def es_dia_habil(d: date) -> bool:
    r = _cache.get(d)
    if r is None:
        r = d.weekday() < 5 and (d.month, d.day) not in FF
        _cache[d] = r
    return r


def _v(d: date) -> tuple[datetime, datetime]:
    return datetime.combine(d, HI), datetime.combine(d, HF)


def horas_habiles_entre(inicio: datetime, fin: datetime) -> float:
    if fin <= inicio:
        return 0.0
    acc = 0.0
    d = inicio.date()
    u = fin.date()
    while d <= u:
        if es_dia_habil(d):
            a, c = _v(d)
            t0 = inicio if inicio > a else a
            t1 = fin if fin < c else c
            acc += (t1 - t0).total_seconds() / 60
        d += timedelta(days=1)
    return round(acc / 60, 2)


def calcular_sla(
    creada_en: datetime,
    horas_limite: int,
    cerrada_en: datetime | None = None,
    ahora: datetime | None = None,
) -> EstadoSla:
    f = cerrada_en or ahora or datetime.now()
    h = horas_habiles_entre(creada_en, f)
    p = round(h / horas_limite, 4) if horas_limite else 0.0
    v = h > horas_limite
    return EstadoSla(
        horas_transcurridas=h,
        horas_limite=horas_limite,
        horas_restantes=round(horas_limite - h, 2),
        porcentaje_consumido=p,
        vencida=v,
        en_riesgo=not v and p >= UMBRAL_RIESGO,
    )
