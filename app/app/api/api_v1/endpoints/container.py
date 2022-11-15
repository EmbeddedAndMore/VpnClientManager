import logging

import docker
from docker.errors import APIError, NotFound
from fastapi import HTTPException
from fastapi.routing import APIRouter

from ....schemas.container_create import (
    ContainerBaseConf,
    ContainerConf,
    ContainerActionResponse,
    ContainerStatus,
)


container_api = APIRouter(prefix="container")
docker_client = docker.from_env()
logger = logging.getLogger(__name__)


@container_api.get("/create", response_model=ContainerActionResponse)
def create_container(container_conf: ContainerConf):
    vols = [f"{key}:{value}" for key, value in container_conf.volume_config.items()]
    container = docker_client.containers.create(
        container_conf.img_name,
        ports=container_conf.port_config,
        volumes=vols,
        name=container_conf.container_name,
        privileged=container_conf.privileged,
    )

    return ContainerActionResponse(status=ContainerStatus.CREATED, msg=container.id)


@container_api.put("/start/{container_id}", response_model=ContainerActionResponse)
def start_container(container_id: str):
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


@container_api.put("/stop/{container_id}", response_model=ContainerActionResponse)
def stop_container(container_id: str):
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


@container_api.put("/remove/{container_id}", response_model=ContainerActionResponse)
def remove_container(container_id: int):
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


@container_api.get("/container}")
def get_containers(container_id: str | None):

    try:
        if container_id:
            container = docker_client.containers.get(container_id)
            return [ContainerConf()]
        else:
            containers = docker_client.containers.list()
    except NotFound as err:
        logger.error(err)
        raise HTTPException(status_code=404, detail="Container not exists.")
    except APIError as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="Error happened while stopping the container."
        )
