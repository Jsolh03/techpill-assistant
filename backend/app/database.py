"""Configuracion de la base de datos (SQLite + SQLAlchemy).

Aqui se crea el "engine" (la conexion), la fabrica de sesiones y la clase Base
de la que heredan los modelos. `get_db` es la dependencia que FastAPI inyecta
en los endpoints para darles una sesion de BD por peticion.
"""
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# El fichero de la base de datos se guarda junto al backend: backend/techpill.db
DB_PATH = Path(__file__).resolve().parent.parent / "techpill.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False es necesario porque FastAPI puede usar varios hilos.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    """Ajustes de SQLite en cada conexion para evitar 'database is locked'."""
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA busy_timeout = 5000")  # espera hasta 5s si esta bloqueada
    cur.execute("PRAGMA foreign_keys = ON")  # respeta las claves foraneas (cascadas)
    cur.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM."""


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: abre una sesion y la cierra al terminar la peticion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea las tablas si no existen. Se llama al arrancar la app."""
    # Importa los modelos para que SQLAlchemy los registre antes de crear tablas.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
