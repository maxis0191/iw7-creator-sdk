"""Offline compatibility checks on the common SDK manifest (no second manifest)."""
from collections import defaultdict


# Source proofs are in COMMUNITY-MOD-DISTRIBUTION.md. Do not infer capability
# from a matching network protocol or let a package extend this reviewed list.
MOD_TRANSPORT_SOURCES = {
    "36f7afedb9e4c8c665b6e29227e3f5c660ed63d6",
    "02a9aeeb89174812fb9a250e437f966239aeba26",
    "77e6d4d24e918ee363b3feee3735c3b889dff7d7",
    "1b76f04e55b7e01ffb9d5a6fd9053585beb5ba27",
}
PROJECT_SOURCE = {"77e6d4d24e918ee363b3feee3735c3b889dff7d7"}
# The stricter project-only rows record the observed fixture baseline. They do
# not claim older clients lack an asset type, nor that a source pin identifies
# project overlays/binary builds. Adding proof is a reviewed code change.
CAPABILITY_SOURCE_PINS = {
    "engine": {"iw7-cp/1": MOD_TRANSPORT_SOURCES, "model-netconststrings/1": PROJECT_SOURCE},
    "client": {"mod-fastfile-download/1": MOD_TRANSPORT_SOURCES,
               "lua-fastfile/1": PROJECT_SOURCE, "xmodel-rigid/1": PROJECT_SOURCE,
               # Fixture upstream only; Native958 private overlay/binary remains
               # a separate prerequisite recorded by the private prop recipe.
               "bo3-mp-static-prop-display/1": PROJECT_SOURCE},
    "server": {"mod-fastfile-host/1": MOD_TRANSPORT_SOURCES,
               "gsc-custom-scripts/1": MOD_TRANSPORT_SOURCES,
               "gsc-private-hud/1": MOD_TRANSPORT_SOURCES, "script-model/1": PROJECT_SOURCE},
}


def check_environment(manifests, *, client_source, server_source, protocol, mode):
    """Check SDK-validated manifests describing the complete intended active set.

    Input pins/protocol are operator assertions, never measurements of a binary
    or remote server. Installed manifests do not prove installed payload hashes.
    """
    errors = []
    if type(protocol) is not int or not 1 <= protocol <= 65535:
        errors.append("A measured integer network protocol is required")
    if protocol != 2 and (client_source in MOD_TRANSPORT_SOURCES or server_source in MOD_TRANSPORT_SOURCES):
        errors.append("Observed protocol differs from the reviewed source protocol 2")
    packages = {}
    namespaces = {}
    destinations = {}
    assets = {}
    client_mods = []
    for manifest in manifests:
        package = manifest["package"]
        ident = package["id"]
        key = ident.casefold()
        if key in packages:
            errors.append("Duplicate active package ID: " + ident)
        packages[key] = manifest
        namespace = manifest["namespace"].casefold()
        if namespace in namespaces:
            errors.append("Namespace collision: " + namespace)
        namespaces[namespace] = ident
        compatibility = manifest["compatibility"]
        if compatibility["engine"] != "iw7" or compatibility["mode"] != mode:
            errors.append("Engine/mode mismatch: " + ident)
        expected_protocol = compatibility["network_protocol"]
        if expected_protocol is not None and expected_protocol != protocol:
            errors.append("Network protocol mismatch: " + ident)
        # Equal protocol is necessary but cannot certify code capabilities.
        native = package["native_requirements"]
        for side, capabilities in manifest["requires"].items():
            for capability in capabilities:
                allowed = CAPABILITY_SOURCE_PINS.get(side, {}).get(capability, set())
                observed = (client_source, server_source) if side == "engine" else (
                    client_source if side == "client" else server_source,)
                if any(pin not in allowed for pin in observed):
                    errors.append("Capability source proof missing: " + side + "/" + capability + " in " + ident)
        for side, observed in (("client", client_source), ("server", server_source)):
            required = native[side + "_source"]
            if required is not None and observed != required:
                errors.append(side + " source mismatch: " + ident)
        if native["client_capabilities"] and client_source not in native["compatible_client_sources"]:
            errors.append("Client capability source mismatch: " + ident)
        delivery = package["delivery"]
        if delivery == "usermap":
            errors.append("Usermap distribution is not implemented by this mod-only packager: " + ident)
        if delivery == "mod":
            client_mods.append(ident)
            if client_source not in MOD_TRANSPORT_SOURCES or server_source not in MOD_TRANSPORT_SOURCES:
                errors.append("Mod transport source pair is not independently reviewed: " + ident)
            if protocol != 2:
                errors.append("Reviewed mod transport requires network protocol 2: " + ident)
        for entry in package["files"]:
            destination = entry["destination"].casefold()
            if destination in destinations:
                errors.append("Active destination collision: " + entry["destination"])
            destinations[destination] = ident
        # Recipient nodes may legitimately be shared. Delivered asset names
        # collide in the engine regardless of the filesystem namespace.
        for node in package["closure"]["nodes"]:
            if node["scope"] == "recipient":
                continue
            asset = (node["kind"], node["id"].casefold())
            if asset in assets:
                errors.append("Delivered asset collision: " + node["id"])
            assets[asset] = ident
    if len(client_mods) > 1:
        errors.append("Only one active fs_game is supported; precompose client dependencies into one package: "
                      + ", ".join(sorted(client_mods)))

    edges = defaultdict(list)
    for key, manifest in packages.items():
        for conflict in manifest["conflicts"]:
            if conflict["id"].casefold() in packages:
                errors.append("Active conflict: " + manifest["package"]["id"] + " / " + conflict["id"])
        for dependency in manifest["dependencies"]:
            target = dependency["id"].casefold()
            found = packages.get(target)
            if found is None:
                errors.append("Missing exact dependency: " + dependency["id"] + "@" + dependency["version"])
            elif found["package"]["version"] != dependency["version"]:
                errors.append("Dependency version mismatch: " + dependency["id"])
            else:
                edges[key].append(target)
    # Iterative traversal avoids recursion failures on long adversarial chains.
    state = {}
    for root in packages:
        stack = [(root, False)]
        while stack:
            key, leaving = stack.pop()
            if leaving:
                state[key] = 2
                continue
            if state.get(key) == 1:
                errors.append("Package dependency cycle at: " + key)
                continue
            if state.get(key) == 2:
                continue
            state[key] = 1
            stack.append((key, True))
            stack.extend((target, False) for target in reversed(edges[key]))
    return errors
