from pydantic import BaseModel, Field, field_validator
from typing import Optional

class BarcelonaCadastralModel(BaseModel):
    """
    Schema for 'Carrec_tipus_propietari.csv'.
    Maps official Catalan headers to English for the Graph.
    """
    year: int = Field(alias="Any")
    district_code: int = Field(alias="Codi_districte")
    district_name: str = Field(alias="Nom_districte")
    neighborhood_code: int = Field(alias="Codi_barri")
    neighborhood_name: str = Field(alias="Nom_barri")
    census_section: int = Field(alias="Seccio_censal")
    owner_type: str = Field(alias="Desc_tipus_propietari") # Subjecte físic / jurídic
    concept: str = Field(alias="Concepte") # Valor_cadastral
    value: float = Field(alias="Valor")

    @field_validator('value', mode='before')
    def parse_value(cls, v):
        if isinstance(v, str):
            try:
                return float(v.replace(',', '.'))
            except ValueError:
                return 0.0
        return v

class BarcelonaSurfaceModel(BaseModel):
    """
    Schema for 'Edificacions_superficie.csv'.
    """
    year: int = Field(alias="Any")
    district_code: int = Field(alias="Codi_districte")
    district_name: str = Field(alias="Nom_districte")
    neighborhood_code: int = Field(alias="Codi_barri")
    neighborhood_name: str = Field(alias="Nom_barri")
    census_section: int = Field(alias="Seccio_censal")
    surface_type: str = Field(alias="Tipus_sup") # Superfície_locals
    surface_m2: float = Field(alias="Superficie_m2")
    
    @field_validator('surface_m2', mode='before')
    def parse_surface(cls, v):
        if isinstance(v, str):
            try:
                return float(v.replace(',', '.'))
            except ValueError:
                return 0.0
        return v
