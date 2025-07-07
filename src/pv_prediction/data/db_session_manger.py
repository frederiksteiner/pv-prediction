from __future__ import annotations

import queue

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

Base = declarative_base()  # pyre-ignore[5]


class FlattenedWeather(Base):  # pyre-ignore[11]
    """Historized weather data."""

    __tablename__: str = "weather"

    lat: sa.Column = sa.Column(sa.Float, primary_key=True)
    lon: sa.Column = sa.Column(sa.Float, primary_key=True)
    date: sa.Column = sa.Column(sa.DateTime, primary_key=True)
    wind_speed_10m: sa.Column = sa.Column(sa.Float)
    wind_dir_10m: sa.Column = sa.Column(sa.Float)
    wind_gusts_10m_1h: sa.Column = sa.Column(sa.Float)
    wind_gusts_10m_24h: sa.Column = sa.Column(sa.Float)
    t_2m: sa.Column = sa.Column(sa.Float)
    t_max_2m_24h: sa.Column = sa.Column(sa.Float)
    t_min_2m_24h: sa.Column = sa.Column(sa.Float)
    msl_pressure: sa.Column = sa.Column(sa.Float)
    precip_1h: sa.Column = sa.Column(sa.Float)
    precip_24h: sa.Column = sa.Column(sa.Float)
    weather_symbol_1h: sa.Column = sa.Column(sa.Integer)
    weather_symbol_24h: sa.Column = sa.Column(sa.Integer)
    uv: sa.Column = sa.Column(sa.Integer)
    sunrise: sa.Column = sa.Column(sa.DateTime)
    sunset: sa.Column = sa.Column(sa.DateTime)


class EngergyTable(Base):
    """History energy information table."""

    __tablename__: str = "energy"

    date: sa.Column = sa.Column(sa.DateTime, primary_key=True)
    produced: sa.Column = sa.Column(sa.Float)
    consumed: sa.Column = sa.Column(sa.Float)
    minus_absolute: sa.Column = sa.Column(sa.Float)
    plus_absolute: sa.Column = sa.Column(sa.Float)
    diff_minus: sa.Column = sa.Column(sa.Float)
    diff_plus: sa.Column = sa.Column(sa.Float)


class PredictionsTable(Base):
    """Table to store the predictions."""

    __tablename__: str = "predictions"

    pv_id: sa.Column = sa.Column(sa.Integer, primary_key=True)
    date: sa.Column = sa.Column(sa.DateTime, primary_key=True)
    prediction_time: sa.Column = sa.Column(sa.DateTime)
    model_id: sa.Column = sa.Column(sa.String)
    energy_produced: sa.Column = sa.Column(sa.Float)


class DBSessionManager:
    """DB session pool manager."""

    initial_pool_size: int = 2
    engine: sa.Engine = sa.create_engine("sqlite:///local_database.db")
    Base.metadata.create_all(engine)
    _session_maker: sessionmaker = sessionmaker(bind=engine)

    _session_pool: queue.Queue[Session] = queue.Queue(initial_pool_size)

    _instance: DBSessionManager | None = None

    def __new__(cls) -> DBSessionManager:
        """Creates a new DBSessionManager."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Inits a new DBSessionManager."""
        self._session_pool = queue.Queue(self.initial_pool_size)
        for _ in range(self.initial_pool_size):
            try:
                session = self._session_maker()
                self._session_pool.put(session)
            except Exception as e:
                print(f"Error creating session: {e}")

    @classmethod
    def get_session(cls) -> Session:
        """This method attempts to retrieve a DB session from the pool.

        - If a session exists in the pool (not empty), it retrieves and returns the session.
        - If the pool is empty (`queue.Empty` exception is raised), it creates a new
          session using `_init_session` and adds it to the pool before returning it.
        """
        try:
            return cls._session_pool.get(block=False)
        except queue.Empty:
            session = cls._session_maker()
            return session

    @classmethod
    def release_session(cls, session: Session) -> None:
        """This method allows releasing a used DB session back to the pool."""
        cls._session_pool.put(session)

    @classmethod
    def close_sessions(cls) -> None:
        """Closes all sessions in the queue."""
        while cls._session_pool.qsize() > 0:
            cls._session_pool.get().close()
