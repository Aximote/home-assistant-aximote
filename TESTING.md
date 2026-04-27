# Local testing

## 1. Run the Aximote backend

From the backend repo, start the API (default port is often **8080** — use whatever your `application.yml` sets). Create a **PAT** via the app or internal tools.

## 2. Expose `custom_components` to Home Assistant

Either copy the folder:

```bash
cp -R custom_components /path/to/ha/config/
```

Or symlink it while developing:

```bash
ln -sf "$(pwd)/custom_components" /path/to/ha/config/custom_components
```

## 3. Home Assistant in Docker (macOS-friendly)

```bash
mkdir -p ~/aximote-ha/config
# symlink or copy custom_components into ~/aximote-ha/config/

docker rm -f homeassistant 2>/dev/null
docker run -d --name homeassistant \
  -v ~/aximote-ha/config:/config \
  -p 8123:8123 \
  ghcr.io/home-assistant/home-assistant:stable
```

Open `http://localhost:8123`, finish onboarding, then **Settings → Devices & services → Add integration → Aximote** and enter your PAT. The integration always calls the production API (`https://api.aximote.com`).

To point Home Assistant at a **local** backend, temporarily change `DEFAULT_BASE_URL` in `custom_components/aximote/const.py` (e.g. `http://host.docker.internal:8080` when HA runs in Docker on Mac/Windows). Linux Docker may need `--add-host=host.docker.internal:host-gateway` on `docker run`. Revert before publishing.

## 4. Debug logging

In `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.aximote: debug
```

## 5. Sanity checks

- After setup, each vehicle should appear as a **device** with a **location** tracker and multiple sensors.
- An account with **no vehicles** should complete setup but create **no devices**; check logs for an informational message from the coordinator.
- Revoke the PAT in the app; within a poll cycle the integration should fail authentication and prompt **reconfigure** (depending on Home Assistant version).
