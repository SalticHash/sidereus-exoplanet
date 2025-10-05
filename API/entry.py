"""
This contains the data class for the exoplanet entries.

This is meant to help access values in a universal format.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto
from API.mathUtils import parseNum

# Disposition types for exoplanets
class Disposition(Enum):
    CANDIDATE = auto()
    CONFIRMED = auto()  # Known planet
    FALSE_POSITIVE = auto()
    AMBIGUOUS_CANDIDATE = auto()

# Class for quantities with values, errors, and units
@dataclass
class Quantity:
    value: float | None = None
    err_upper: float | None = None
    err_lower: float | None = None
    units: str | None = None
    
    @classmethod
    def from_dict(cls, data: dict | str | None, default_units: str | None = None) -> "Quantity":
        if data is str or data is float:
            return cls.from_value(cls, parseNum(data), default_units)
            
        if not data:
            return cls(units=default_units)
        return cls(
            value=parseNum(data.get("value")),
            err_upper=parseNum(data.get("err_upper")),
            err_lower=parseNum(data.get("err_lower")),
            units=data.get("units", default_units),
        )
    
    @classmethod
    def from_value(cls, value: float | None, default_units: str | None = None) -> "Quantity":
        return cls(
            value,
            err_upper=0.0,
            err_lower=0.0,
            units=default_units,
        )

# Main class for exoplanet entries
@dataclass
class ExoplanetEntry:
    # Identifiers
    id: Optional[str] = None                # tid / kepid
    name: Optional[str] = None              # toi / kepoi_name / kepler_name
    disposition: Optional[str] = None       # tfopwg_disp / koi_disposition / koi_pdisposition
    score: Optional[float] = None           # koi_score

    # Position
    ra: Optional[float] = None              # RA [deg]
    dec: Optional[float] = None             # Dec [deg]

    # Planetary properties
    orbital_period: Quantity = field(default_factory=lambda: Quantity(units="days"))
    transit_epoch: Quantity = field(default_factory=lambda: Quantity(units="BJD"))   # or BKJD for Kepler
    transit_duration: Quantity = field(default_factory=lambda: Quantity(units="hours"))
    transit_depth: Quantity = field(default_factory=lambda: Quantity(units="ppm"))
    planet_radius: Quantity = field(default_factory=lambda: Quantity(units="R_Earth"))
    equilibrium_temp: Quantity = field(default_factory=lambda: Quantity(units="K"))
    insolation: Quantity = field(default_factory=lambda: Quantity(units="Earth flux"))

    # Stellar properties
    stellar_temp: Quantity = field(default_factory=lambda: Quantity(units="K"))
    stellar_logg: Quantity = field(default_factory=lambda: Quantity(units="cm/s^2"))
    stellar_radius: Quantity = field(default_factory=lambda: Quantity(units="R_Sun"))

    # Metadata
    created: Optional[str] = None           # toi_created
    updated: Optional[str] = None           # rowupdate / koi_tce_delivname
    
    @classmethod
    def from_dict(cls, dict) -> "ExoplanetEntry":
        return cls(
            id=dict.get("id"),
            name=dict.get("name"),
            disposition=dict.get("disposition"),
            score=parseNum(dict.get("score")),
            ra=parseNum(dict.get("ra")),
            dec=parseNum(dict.get("dec")),

            orbital_period=Quantity.from_dict(dict.get("orbital_period"), "days"),
            transit_epoch=Quantity.from_dict(dict.get("transit_epoch"), "BJD"),
            transit_duration=Quantity.from_dict(dict.get("transit_duration"), "hours"),
            transit_depth=Quantity.from_dict(dict.get("transit_depth"), "ppm"),
            planet_radius=Quantity.from_dict(dict.get("planet_radius"), "R_Earth"),
            equilibrium_temp=Quantity.from_dict(dict.get("equilibrium_temp"), "K"),
            insolation=Quantity.from_dict(dict.get("insolation"), "Earth flux"),

            stellar_temp=Quantity.from_dict(dict.get("stellar_temp"), "K"),
            stellar_logg=Quantity.from_dict(dict.get("stellar_logg"), "cm/s^2"),
            stellar_radius=Quantity.from_dict(dict.get("stellar_radius"), "R_Sun"),

            created=dict.get("created"),
            updated=dict.get("updated"),
        )

# Dataset types for classification
class DatasetType(Enum):
    UNKNOWN = auto()
    KOI = auto()
    TOI = auto()
    K2 = auto()

# Class to store exoplanet entries and dataset type
@dataclass
class ExoplanetData:
    entries: list[ExoplanetEntry]  
    dataset_type: DatasetType = field(default_factory=lambda: DatasetType.UNKNOWN)
