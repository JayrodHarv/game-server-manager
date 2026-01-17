import docker

client = docker.from_env()

_attached_stdin = {}

def start_container(
    name: str,
    image: str,
    env: dict,
    ports: list[int]
):
    port_map = {f"{p}/tcp": p for p in ports}

    return client.containers.run(
        image=image,
        name=name,
        environment=env,
        ports=port_map,
        detach=True,
        stdin_open=True,
        tty=True,
        restart_policy={"Name": "unless-stopped"},
    )

def get_container(name: str):
    return client.containers.get(name)

def get_stdin_socket(container):
    if container.id not in _attached_stdin:
        sock = container.attach_socket(
            params={
                "stdin": 1,
                "stream": 1
            }
        )
        _attached_stdin[container.id] = sock
    return _attached_stdin[container.id]