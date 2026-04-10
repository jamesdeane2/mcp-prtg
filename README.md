# mcp-prtg

MCP server for the PRTG Network Monitor API. Provides tools for querying probes, groups, devices, sensors, alerts, and historical data.

## Setup

```bash
cp .env.example .env
# Edit .env with your PRTG credentials
```

## Configuration

| Variable | Description |
|---|---|
| `PRTG_BASE_URL` | PRTG server URL (e.g. `https://your-instance.my-prtg.com`) |
| `PRTG_API_TOKEN` | API token from PRTG (Setup > Account Settings > API Keys) |

## Tools

| Tool | Description |
|---|---|
| `prtg_list_probes` | List all probes (client sites/locations) |
| `prtg_list_groups` | List groups with optional probe filter |
| `prtg_list_devices` | List devices with optional group/probe filter |
| `prtg_list_sensors` | List sensors with optional device/group/status filter |
| `prtg_get_device_details` | Get full details for a device by object ID |
| `prtg_get_sensor_details` | Get full details for a sensor by object ID |
| `prtg_get_sensor_history` | Get historical data for a sensor |
| `prtg_get_alerts` | Get current alerts/log messages |
| `prtg_get_tree` | Get hierarchical device tree |
| `prtg_search_devices` | Search devices by name |

## Usage with MCP Gateway

```json
{
  "prtg": {
    "command": "/opt/homebrew/bin/uv",
    "args": ["--directory", "/path/to/mcp-prtg", "run", "mcp-prtg"]
  }
}
```
