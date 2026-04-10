"""FastMCP server for PRTG Network Monitor."""

import json

from mcp.server.fastmcp import FastMCP

from .client import PRTGClient, PRTGError, get_client

mcp = FastMCP("PRTG Network Monitor")


def _json(data) -> str:
    """Format data as indented JSON string."""
    return json.dumps(data, indent=2, default=str)


def _error(message: str) -> str:
    """Format an error response."""
    return json.dumps({"error": message}, indent=2)


def register_tools(client: PRTGClient | None = None) -> None:
    """Register all PRTG tools with the MCP server."""
    client = client or get_client()

    @mcp.tool()
    async def prtg_list_probes() -> str:
        """List all PRTG probes. Probes typically represent client sites or locations.

        Returns:
            JSON array of probes with objid, name, active, status, and message.
        """
        try:
            records = await client.table(
                content="probes",
                columns="objid,name,active,status,message"
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_list_groups(probe_name: str | None = None) -> str:
        """List PRTG groups with optional filtering by probe name.

        Groups organize devices and often represent clients or logical groupings.

        Args:
            probe_name: Filter groups belonging to this probe (substring match)

        Returns:
            JSON array of groups with objid, name, group, probe, active, status.
        """
        try:
            filters = {}
            if probe_name:
                filters["filter_probe"] = f"@sub({probe_name})"
            records = await client.table(
                content="groups",
                columns="objid,name,group,probe,active,status",
                filters=filters
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_list_devices(
        group: str | None = None,
        probe: str | None = None
    ) -> str:
        """List PRTG devices with optional filtering.

        Args:
            group: Filter by group name (substring match)
            probe: Filter by probe name (substring match)

        Returns:
            JSON array of devices with objid, name, group, probe, host, active, status, message.
        """
        try:
            filters = {}
            if group:
                filters["filter_group"] = f"@sub({group})"
            if probe:
                filters["filter_probe"] = f"@sub({probe})"
            records = await client.table(
                content="devices",
                columns="objid,name,group,probe,host,active,status,message",
                filters=filters
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_list_sensors(
        device: str | None = None,
        group: str | None = None,
        status: str | None = None
    ) -> str:
        """List PRTG sensors with optional filtering.

        Args:
            device: Filter by device name (substring match)
            group: Filter by group name (substring match)
            status: Filter by status — use "up", "down", "warning", "paused", or "unknown"

        Returns:
            JSON array of sensors with objid, device, sensor, group, probe, status, message, lastvalue, priority.
        """
        try:
            filters = {}
            if device:
                filters["filter_device"] = f"@sub({device})"
            if group:
                filters["filter_group"] = f"@sub({group})"
            if status:
                status_map = {
                    "up": "2",
                    "warning": "4",
                    "down": "5",
                    "paused": "7",
                    "unknown": "0"
                }
                status_val = status_map.get(status.lower(), status)
                filters["filter_status"] = status_val
            records = await client.table(
                content="sensors",
                columns="objid,device,sensor,group,probe,status,message,lastvalue,priority",
                filters=filters
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_get_device_details(objid: int) -> str:
        """Get detailed information for a specific device by its object ID.

        Args:
            objid: The PRTG object ID of the device

        Returns:
            JSON with full device details.
        """
        try:
            records = await client.table(
                content="devices",
                columns="objid,name,group,probe,host,active,status,message,"
                        "favorite,interval,access,dependency,position,comments",
                count=1,
                extra_params={"id": objid}
            )
            if records:
                return _json(records[0])
            return _error(f"Device with objid {objid} not found")
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_get_sensor_details(objid: int) -> str:
        """Get detailed information for a specific sensor by its object ID.

        Args:
            objid: The PRTG object ID of the sensor

        Returns:
            JSON with full sensor details including last value.
        """
        try:
            records = await client.table(
                content="sensors",
                columns="objid,device,sensor,group,probe,status,message,"
                        "lastvalue,priority,favorite,interval,access,"
                        "dependency,position,comments",
                count=1,
                extra_params={"id": objid}
            )
            if records:
                return _json(records[0])
            return _error(f"Sensor with objid {objid} not found")
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_get_sensor_history(
        sensor_id: int,
        average: int = 300,
        start_date: str | None = None,
        end_date: str | None = None
    ) -> str:
        """Get historical data for a sensor.

        Args:
            sensor_id: The PRTG object ID of the sensor
            average: Averaging interval in seconds (default 300 = 5 minutes)
            start_date: Start date in format YYYY-MM-DD-HH-MM-SS
            end_date: End date in format YYYY-MM-DD-HH-MM-SS

        Returns:
            JSON array of historical data points.
        """
        try:
            records = await client.historic_data(
                sensor_id=sensor_id,
                average=average,
                start_date=start_date,
                end_date=end_date
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_get_alerts(status: str | None = None) -> str:
        """Get current alerts and log messages from PRTG.

        Args:
            status: Filter by message type — "warning", "error", or "down"

        Returns:
            JSON array of alert/log messages.
        """
        try:
            filters = {}
            if status:
                status_map = {
                    "warning": "4",
                    "error": "5",
                    "down": "5"
                }
                status_val = status_map.get(status.lower(), status)
                filters["filter_status"] = status_val
            records = await client.table(
                content="messages",
                columns="objid,datetime,parent,status,sensor,device,group,"
                        "probe,message",
                filters=filters
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_get_tree(probe_name: str | None = None) -> str:
        """Get the PRTG device tree: probes -> groups -> devices -> sensor counts.

        Builds a hierarchical view of the monitoring infrastructure.

        Args:
            probe_name: Optionally limit to a specific probe (substring match)

        Returns:
            JSON tree structure showing the monitoring hierarchy.
        """
        try:
            # Get probes
            probe_filters = {}
            if probe_name:
                probe_filters["filter_name"] = f"@sub({probe_name})"
            probes = await client.table(
                content="probes",
                columns="objid,name,active,status",
                filters=probe_filters
            )

            # Get all groups
            groups = await client.table(
                content="groups",
                columns="objid,name,probe,active,status",
                count=2500
            )

            # Get all devices
            devices = await client.table(
                content="devices",
                columns="objid,name,group,probe,host,status",
                count=2500
            )

            # Get sensor counts per device
            sensors = await client.table(
                content="sensors",
                columns="objid,device,status",
                count=10000
            )

            # Build sensor count map: device_name -> {up, down, warning, total}
            sensor_counts: dict[str, dict] = {}
            for s in sensors:
                dev = s.get("device", "")
                if dev not in sensor_counts:
                    sensor_counts[dev] = {"up": 0, "down": 0, "warning": 0, "paused": 0, "total": 0}
                sensor_counts[dev]["total"] += 1
                st = str(s.get("status", "")).lower()
                if "up" in st:
                    sensor_counts[dev]["up"] += 1
                elif "down" in st:
                    sensor_counts[dev]["down"] += 1
                elif "warn" in st:
                    sensor_counts[dev]["warning"] += 1
                elif "paus" in st:
                    sensor_counts[dev]["paused"] += 1

            # Build tree
            tree = []
            for probe in probes:
                probe_node = {
                    "objid": probe["objid"],
                    "name": probe["name"],
                    "status": probe.get("status", ""),
                    "groups": []
                }
                probe_groups = [g for g in groups
                                if g.get("probe", "") == probe["name"]]
                for grp in probe_groups:
                    group_node = {
                        "objid": grp["objid"],
                        "name": grp["name"],
                        "status": grp.get("status", ""),
                        "devices": []
                    }
                    group_devices = [d for d in devices
                                     if d.get("group", "") == grp["name"]
                                     and d.get("probe", "") == probe["name"]]
                    for dev in group_devices:
                        device_node = {
                            "objid": dev["objid"],
                            "name": dev["name"],
                            "host": dev.get("host", ""),
                            "status": dev.get("status", ""),
                            "sensors": sensor_counts.get(dev["name"], {"total": 0})
                        }
                        group_node["devices"].append(device_node)
                    probe_node["groups"].append(group_node)
                tree.append(probe_node)

            return _json(tree)
        except PRTGError as e:
            return _error(e.message)

    @mcp.tool()
    async def prtg_search_devices(name: str) -> str:
        """Search for PRTG devices by name.

        Args:
            name: Search term (substring match against device name)

        Returns:
            JSON array of matching devices.
        """
        try:
            records = await client.table(
                content="devices",
                columns="objid,name,group,probe,host,active,status,message",
                filters={"filter_name": f"@sub({name})"}
            )
            return _json(records)
        except PRTGError as e:
            return _error(e.message)


def main():
    """Run the MCP server."""
    register_tools()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
