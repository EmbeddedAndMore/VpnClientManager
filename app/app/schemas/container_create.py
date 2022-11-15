from enum import StrEnum
from pydantic import BaseModel


class ContainerBaseConf(BaseModel):
    container_name: str  # The name we set/query for the container


class ContainerConf(ContainerBaseConf):
    img_name: str  # name of docker image
    port_config: dict[
        int, int
    ]  # expose port {host_port:container_port} . will be added as `-p host_port:container_port`
    volume_config: dict[
        str, str
    ]  # expose volumes {host_vol:container_vol}. will be added as `-v host_vol:container_vol`
    privileged: bool  # if container need to be run in privileged mode


class ContainerStatus(StrEnum):
    CREATED = "Created"
    RUN = "Run"
    STARTED = "Started"
    STOPPED = "Sropped"
    REMOVED = "Removed"


class ContainerActionResponse(BaseModel):
    status: ContainerStatus
    msg: str
    error: str = ""

