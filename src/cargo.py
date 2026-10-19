"""Read Cargo package dependencies from the crates.io HTTP API."""

import json
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class CargoRegistryError(Exception):
    """Represent an error returned while reading the registry."""


def fetch_json(url):
    """Fetch and decode one JSON response from the registry."""
    request = Request(url, headers={"User-Agent": "dependency-graph-lab/1.0"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except (URLError, json.JSONDecodeError) as error:
        raise CargoRegistryError(f"Registry request failed: {error}") from error


def fetch_direct_dependencies(package, repository, version=None):
    """Return normal and build dependencies for a selected crate version."""
    base_url = repository.rstrip("/")
    package_path = quote(package, safe="")
    if version is None:
        crate_url = f"{base_url}/api/v1/crates/{package_path}"
        crate = fetch_json(crate_url).get("crate", {})
        version = crate.get("max_stable_version") or crate.get("max_version")
        if not version:
            raise CargoRegistryError(
                f"No published version found for {package}"
            )

    version_path = quote(version, safe="")
    dependency_url = (
        f"{base_url}/api/v1/crates/{package_path}/{version_path}/dependencies"
    )
    dependencies = fetch_json(dependency_url).get("dependencies", [])
    names = {
        item["crate_id"]
        for item in dependencies
        if item.get("kind") in (None, "normal", "build")
    }
    return sorted(names)