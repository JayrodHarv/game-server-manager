import docker

client = docker.from_env()

def list_containers():
    return client.containers.list(all=True)

def get_container(name: str):
    return client.containers.get(name)

def run_container(
    image: str,
    name: str,
    ports: dict,
    volumes: dict,
    memory: str = "2g",
    cpus: float = 1.0,
    env: dict = None,
):
    env = env or {}

    return client.containers.run(
        image,
        name=name,
        detach=True,
        ports=ports,
        environment={
            "EULA": "TRUE",
            **env,
        },
        volumes=volumes,
        mem_limit=memory,
        cpu_quota=int(cpus * 100000),
        restart_policy={"Name": "unless-stopped"},
    )
