from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path


class ContainerBaseConf(BaseModel):
    id: str | None = Field(
        default=None,
        title="For creating container this field is empty. For querying container this field will be filled.",
        example=None,
    )
    container_name: str = Field(
        example="ocserv"
    )  # The name we set/query for the container


class ContainerConf(ContainerBaseConf):

    img_name: str = Field(example="pezhvak/ocserv:latest")  # name of docker image
    port_config: dict[str, tuple[str, int]] = Field(
        example={"443/tcp": ("0.0.0.0", 443), "443/udp": ("0.0.0.0", 443)}
    )  # expose port {container_port:host_port} . will be added as `-p host_port:container_port` like {'2222/tcp': 3333}
    volume_config: dict[Path, Path] = Field(
        example={"/Users/marmoun/Projects/data": "/etc/ocserv/data"}
    )  # expose volumes {host_vol:container_vol}. will be added as `-v host_vol:container_vol`
    privileged: bool = Field(
        example=True
    )  # if container need to be run in privileged mode


class ContainerStatus(str, Enum):
    CREATED = "Created"
    RUN = "Run"
    STARTED = "Started"
    STOPPED = "Sropped"
    REMOVED = "Removed"


class ContainerActionResponse(BaseModel):
    status: ContainerStatus
    msg: str
    error: str = ""

