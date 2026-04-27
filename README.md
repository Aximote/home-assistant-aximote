# Aximote Home Assistant integration

Custom integration for [Home Assistant](https://www.home-assistant.io/) that connects to the **Aximote public API** using a **personal access token (PAT)**. Use it to expose vehicle location, fuel/battery levels, trip summaries, and refuel/charge data as entities.

## Requirements

- Home Assistant **2024.6** or newer (see `hacs.json`).
- An Aximote account with **Pro** (PATs are a Pro feature; tokens may be revoked if the subscription lapses).
- A **personal access token**. PAT creation is available in the Aximote app for Pro users (exact menu path may depend on app version). If you cannot create a token yet, use a build or channel where PAT issuance is enabled.

## Install (HACS — default catalog)

When this integration is listed in the HACS default store:

1. Open **HACS → Integrations**.
2. Search for **Aximote** and download it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for **Aximote**.

## Install (HACS — custom repository)

Until the integration is in the default catalog (or for a fork):

1. In HACS, open **⋮ → Custom repositories**.
2. Add this repository URL, category **Integration**.
3. Install **Aximote** from the HACS **Integrations** tab.
4. Restart Home Assistant.
5. Add the integration under **Settings → Devices & services**.

A **public** GitHub repository and **release tags** (e.g. `v0.1.0` matching `manifest.json` `version`) are recommended so HACS can install stable versions.

## Install (manual)

Copy the `custom_components/aximote` folder into your Home Assistant configuration directory:

```text
<config>/custom_components/aximote/
```

Restart Home Assistant, then add the integration from the UI.

## Configuration

The config flow asks for **one** field:

- **Personal access token** — paste the PAT. It is stored in Home Assistant’s config entry (same as other integrations).

The integration **always** uses the production API base URL **`https://api.aximote.com`** defined in code (`custom_components/aximote/const.py`). There is no UI to change the URL. For a **local or staging** backend, developers can temporarily change `DEFAULT_BASE_URL` in `const.py` — see [TESTING.md](TESTING.md).

## Entities

For each vehicle, the integration creates:

- **Device tracker** — GPS from the latest vehicle state (when location is available).
- **Binary sensors** — on trip, ignition (when reported).
- **Sensors** — fuel level %, battery %, range, odometer, speed, bearing, capture time, current trip id, vehicle profile fields (make, model, year, capacities, etc.), last trip metrics, last refuel/charge metrics.

If the API returns **no vehicles** for your account, the integration stays healthy but **no devices** are created until at least one vehicle exists.

`null` values from the API show as **unavailable** for that update (no fake zeros).

## Troubleshooting

- **Invalid token** — regenerate a PAT; revoked or expired tokens return 401 and Home Assistant may prompt for re-authentication.
- **Pro required** — the API returns 402 if the account is not entitled; renew or upgrade Pro as applicable.
- **Cannot connect** — check that `https://api.aximote.com` is reachable from the Home Assistant host (firewall, DNS, TLS inspection). For self-hosted API testing, see [TESTING.md](TESTING.md).
- **Rate limiting** — the public API may return 429; the integration surfaces this as a temporary update failure.
- **No devices** — confirm vehicles exist in the Aximote app for the same account as the PAT.

## Development & local testing

See [TESTING.md](TESTING.md) for Docker-based Home Assistant testing and pointing at a local backend.

## License

MIT — see [LICENSE](LICENSE).
