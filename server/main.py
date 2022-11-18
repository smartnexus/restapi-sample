from typing import Union, List
from enum import IntEnum, Enum

from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI()
save = False

# ================ Persistance layer ================

@app.on_event("startup")
def startup_event():
    with open("data/personas.json", "r") as dump_file:
        global personas
        jsonarr = json.load(dump_file)
        personas = [Persona(**item) for item in jsonarr]

    with open("data/proyectos.json", "r") as dump_file:
        global proyectos
        jsonarr = json.load(dump_file)
        proyectos = [Proyecto(**item) for item in jsonarr]

    with open("data/reuniones.json", "r") as dump_file:
        global reuniones
        jsonarr = json.load(dump_file)
        reuniones = [Reunion(**item) for item in jsonarr]

@app.on_event("shutdown")
def shutdown_event():
    if len(personas) > 0 and save:
        with open("data/personas.json", "w") as dump_file:
            jsonarr = [m.dict() for m in personas]
            json.dump(jsonarr, dump_file)
    
    if len(proyectos) > 0 and save:
        with open("data/proyectos.json", "w") as dump_file:
            jsonarr = [m.dict() for m in proyectos]
            json.dump(jsonarr, dump_file)

    if len(reuniones) > 0 and save:
        with open("data/reuniones.json", "w") as dump_file:
            jsonarr = [m.dict() for m in reuniones]
            json.dump(jsonarr, dump_file)

# ================ Data layer ================

def actualizarReuniones(new):
    global reuniones
    reuniones = new

def actualizarProyectos(new):
    global proyectos
    proyectos = new

def actualizarPersonas(new):
    global personas
    personas = new

class Persona(BaseModel):
    dni: str
    nombre: str
    apellidos: str
    telefono: str
    email: str
    departamento: Union[str, bool] = False

class TipoProyecto(IntEnum):
    album = 1
    single = 2

class Proyecto(BaseModel):
    identificador: int
    entrada: int
    personas: List[str]
    genero: str
    tipo: TipoProyecto
    aceptado: bool = False

class CambioProyecto(BaseModel):
    aceptado: bool

class TipoReunion(IntEnum):
    presentacion_artista = 1 # Presentación con el artista
    presentacion_emp = 2     # Presentación de estrategia al artista
    presentacion_dpto = 3    # Presentación con el departamento
    firma_contrato = 4       # Firma del contrato

class Orden(str, Enum):
    Asc = 'asc'
    Desc = 'desc'

class Reunion(BaseModel):
    identificador: int
    convocatoria: int
    titulo: TipoReunion
    lugar: str
    convocados: List[str]
    proyecto: int

# ================ API layer ================

@app.get("/personas")
def obtener_personas(dpto: Union[str, bool] = None):
    if dpto is None:
        return personas
    else:
        return [p for p in personas if str(p.departamento).lower() == str(dpto).lower()]
@app.post("/personas")
def insertar_persona(persona: Persona):
    source = personas.copy()
    if all(p.dni != persona.dni for p in personas):
        source.append(persona)
        actualizarPersonas(source)
    return personas

@app.delete("/reuniones/{identificador_reunion}/personas/{identificador_persona}")
def eliminar_reunion_persona(identificador_persona: str, identificador_reunion: int):
    source = reuniones.copy()
    reunion = [r for r in source if r.identificador == identificador_reunion]
    if len(reunion) > 0:
        convocados = reunion[0].convocados
        reunion[0].convocados = [c for c in convocados if c != identificador_persona]
    return [r for r in reuniones if r.identificador == identificador_reunion]

@app.get("/proyectos")
def obtener_proyectos(aceptado: bool = None, tipo: int = None):
    if aceptado is None and tipo is None:
        return proyectos
    elif aceptado is not None and tipo is None:
        return [p for p in proyectos if p.aceptado == aceptado]
    elif aceptado is None and tipo is not None:
        return [p for p in proyectos if p.tipo == tipo]
    else:
        return [p for p in proyectos if p.aceptado == aceptado and p.tipo == tipo]
@app.post("/proyectos")
def insertar_proyecto(proyecto: Proyecto):
    source = proyectos.copy()
    if all(p.identificador != proyecto.identificador for p in proyectos):
        source.append(proyecto)
        actualizarProyectos(source)
    return proyectos
@app.put("/proyectos/{identificador_proyecto}")
def modificar_proyecto(identificador_proyecto: int, cambioProyecto: CambioProyecto):
    source = proyectos.copy()
    proyecto = [p for p in source if p.identificador == identificador_proyecto]
    if len(proyecto) > 0:
        proyecto[0].aceptado = cambioProyecto.aceptado
    return [p for p in proyectos if p.identificador == identificador_proyecto]

@app.get("/reuniones")
@app.get("/proyectos/{identificador_proyecto}/reuniones")
@app.get("/personas/{identificador_persona}/reuniones")
def obtener_reuniones(identificador_proyecto: int = None, identificador_persona: str = None, orden: str = Orden.Desc):
    salida = reuniones

    if identificador_proyecto is not None:
        salida = [r for r in reuniones if r.proyecto == identificador_proyecto]
    
    if identificador_persona is not None:
        salida = [r for r in reuniones if any(c == identificador_persona for c in r.convocados)]

    if orden == Orden.Asc:
        return sorted(salida, key=lambda r: r.convocatoria)
    elif orden == Orden.Desc:
        return sorted(salida, key=lambda r: r.convocatoria, reverse=True)
@app.delete("/proyectos/{identificador_proyecto}/reuniones/{identificador_reunion}")
def eliminar_reunion_proyecto(identificador_proyecto: int, identificador_reunion: int):
    source = reuniones.copy()
    actualizarReuniones([r for r in source if r.identificador != identificador_reunion or r.proyecto != identificador_proyecto])
    return [r for r in reuniones if r.proyecto == identificador_proyecto]





