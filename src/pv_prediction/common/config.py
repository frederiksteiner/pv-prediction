import dataclasses
import os


@dataclasses.dataclass()
class MeteomaticsConfig:
    """Meteomatics related configs."""

    username: str = ""
    password: str = ""
    base_url: str = "api.meteomatics.com"


@dataclasses.dataclass()
class FroniusConfig:
    """Fronius related configs."""

    ip_adress: str = ""


@dataclasses.dataclass()
class Config:
    """Global config."""

    meteo: MeteomaticsConfig = dataclasses.field(default_factory=MeteomaticsConfig)
    fronius: FroniusConfig = dataclasses.field(default_factory=FroniusConfig)


def resolve_config() -> Config:
    """Resolve config."""
    default_config = Config()

    default_config.meteo.username = str(os.getenv("METEO_USERNAME"))
    default_config.meteo.password = str(os.getenv("METEO_PASSWORD"))

    default_config.fronius.ip_adress = str(os.getenv("FRONIUS_IP"))
    return default_config
