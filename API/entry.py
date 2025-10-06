from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DatasetType(Enum):
    # Dataset types were defined
    # Se definieron los tipos de conjunto de datos
    UNKNOWN = 0
    KOI = 1
    TOI = 2
    K2 = 3


class Disposition(Enum):
    # Possible exoplanet dispositions were listed
    # Se enumeraron las posibles disposiciones de exoplanetas
    CONFIRMED = "CONFIRMED"
    CANDIDATE = "CANDIDATE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    AMBIGUOUS_CANDIDATE = "AMBIGUOUS_CANDIDATE"


@dataclass
class Quantity:
    # Quantity class was created to store numeric values with units
    # Se creó la clase Quantity para almacenar valores numéricos con unidades
    value: Optional[float] = None
    units: Optional[str] = None

    @staticmethod
    def from_value(value: Optional[float], units: Optional[str]) -> "Quantity":
        # Quantity object was built from value and units
        # Se construyó un objeto Quantity a partir del valor y las unidades
        return Quantity(value, units)


@dataclass
class ExoplanetEntry:
    # Exoplanet entry structure was defined
    # Se definió la estructura de una entrada de exoplaneta
    id: Optional[str] = None
    name: Optional[str] = None
    disposition: Optional[str] = None
    score: Optional[float] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    orbital_period: Optional[Quantity] = None
    transit_epoch: Optional[Quantity] = None
    transit_duration: Optional[Quantity] = None
    transit_depth: Optional[Quantity] = None
    planet_radius: Optional[Quantity] = None
    equilibrium_temp: Optional[Quantity] = None
    insolation: Optional[Quantity] = None
    stellar_temp: Optional[Quantity] = None
    stellar_logg: Optional[Quantity] = None
    stellar_radius: Optional[Quantity] = None
    created: Optional[str] = None
    updated: Optional[str] = None


@dataclass
class ExoplanetData:
    # Dataset container for all entries was defined
    # Se definió el contenedor del conjunto de datos para todas las entradas
    entries: list[ExoplanetEntry]
    dataset_type: DatasetType

    # Iterable behavior was implemented
    # Se implementó el comportamiento iterable
    def __iter__(self):
        return iter(self.entries)
