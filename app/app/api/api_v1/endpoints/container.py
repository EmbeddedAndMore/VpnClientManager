import logging

import docker
from docker.models.containers import Container
from docker.errors import APIError, NotFound, ImageNotFound
from fastapi import HTTPException
from fastapi.routing import APIRouter

from ....schemas.container_create import (
    ContainerBaseConf,
    ContainerConf,
    ContainerActionResponse,
    ContainerStatus,
)


router = APIRouter()
docker_client = docker.from_env()
logger = logging.getLogger(__name__)


def get_container_port_config(container: Container):
    """Extract and port config from container's attrs.
    
    format is {container_port: (host_ip, host_port), ...}
    """
    return {
        cconf: (hconf[0]["HostIp"], int(hconf[0]["HostPort"]))
        for cconf, hconf in container.attrs["HostConfig"]["PortBindings"].items()
    }


def get_container_volume_config(container: Container):
    """Extract and return volumes config from container's attrs.
    
    format is {host_dir:container_dir, ...}
    """
    return {m["Source"]: m["Destination"] for m in container.attrs["Mounts"]}


@router.post("/create", response_model=ContainerActionResponse)
def create_container(container_conf: ContainerConf):
    """Create a container without starting it."""
    vols = [f"{key}:{value}" for key, value in container_conf.volume_config.items()]
    try:
        images = docker_client.images.get(container_conf.img_name)
    except ImageNotFound:
        docker_client.images.pull(container_conf.img_name)

    try:
        container = docker_client.containers.create(
            container_conf.img_name,
            ports=container_conf.port_config,
            volumes=vols,
            name=container_conf.container_name,
            privileged=container_conf.privileged,
        )
    except (ImageNotFound, APIError) as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="Error happened while creating the container."
        )

    return ContainerActionResponse(status=ContainerStatus.CREATED, msg=container.id)


@router.put("/start/{container_id}", response_model=ContainerActionResponse)
def start_container(container_id: str):
    """Start a container that is already created."""
    try:
        container = docker_client.containers.get(container_id)
        container.start()
    except NotFound:
        raise HTTPException(status_code=404, detail="Container not exists.")
    except APIError as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="Error happened while starting the container."
        )
    return ContainerActionResponse(status=ContainerStatus.STARTED, msg=container.id)


@router.put("/stop/{container_id}", response_model=ContainerActionResponse)
def stop_container(container_id: str):
    """Stop the container with the matched ID."""
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
    except NotFound as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Container not exists.")
    except APIError as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="Error happened while stopping the container."
        )

    return ContainerActionResponse(status=ContainerStatus.STOPPED, msg=container.id)


@router.put("/remove/{container_id}", response_model=ContainerActionResponse)
def remove_container(container_id: str):
    """Remove the container with the matched ID."""
    try:
        container = docker_client.containers.get(container_id)
        if container.status == "running":
            stop_container(container_id)
        container.remove()
    except NotFound as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Container not exists.")
    except APIError as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="Error happened while removing the container."
        )
    return ContainerActionResponse(status=ContainerStatus.REMOVED, msg="")


@router.get("/", response_model=list[ContainerConf])
def get_containers(container_id: str | None = None):
    """Return the container with the matched ID or all of them if no ID is given."""

    try:
        if container_id:
            container = docker_client.containers.get(container_id)
            containers = [container]
        else:
            containers = docker_client.containers.list(all=True)
        result = []
        for cont in containers:
            port_confs = get_container_port_config(cont)
            volume_confs = get_container_volume_config(cont)
            result.append(
                ContainerConf(
                    id=cont.id,
                    container_name=cont.name,
                    img_name=cont.image.attrs["RepoTags"][0],
                    port_config=port_confs,
                    volume_config=volume_confs,
                    privileged=True,
                )
            )
        return result
    except NotFound as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Container not exists.")
    except APIError as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="Error happened while stopping the container."
        )

