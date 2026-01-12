## Game Server Manager

### Start
```bash
docker compose up -d --build

## Create a Minecraft server
```bash
curl -X POST http://localhost:8000/servers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mc-test",
    "port": 25565,
    "memory": "4g",
    "cpus": 2
  }'

# Create a Minecraft server with RCON enabled
```bash
curl -X POST http://localhost:8000/servers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mc-test-rcon",
    "port": 25565,
    "rcon_port": 25575,
    "rcon_password": "super-secret",
    "memory": "4g",
    "cpus": 2
  }'

# Connect to console (WebSocket) and send commands
```bash
# using wscat
wscat -c ws://localhost:8000/ws/servers/mc-test-rcon
# then type Minecraft commands (e.g. 'say hello')
```

Note: RCON must be enabled for the container (the server will be started with RCON enabled when you pass `rcon_password` during server creation). If you don't provide RCON credentials, commands will be executed inside the container as separate processes (fallback behavior).


# Start a server
curl -X POST http://localhost:8000/servers/{insert_server_name}/start

# Delete a server
```bash
# graceful delete (will attempt to stop first):
curl -X DELETE http://localhost:8000/servers/{insert_server_name}

# force delete (remove even if stop fails):
curl -X DELETE "http://localhost:8000/servers/{insert_server_name}?force=true"
```

# Update server settings
```bash
# update memory and CPU
curl -X POST http://localhost:8000/servers/{insert_server_name}/update \
  -H "Content-Type: application/json" \
  -d '{ "memory": "6g", "cpus": 2 }'

# enable/change RCON
curl -X POST http://localhost:8000/servers/{insert_server_name}/update \
  -H "Content-Type: application/json" \
  -d '{ "rcon_password": "new-secret", "rcon_port": 25576 }'
```

# RCON diagnostic
```bash
# quick RCON test (returns list output or error):
curl http://localhost:8000/servers/{insert_server_name}/rcon_test
```

## View Logs
```bash
curl http://localhost:8000/servers/{insert_server_name}/logs
