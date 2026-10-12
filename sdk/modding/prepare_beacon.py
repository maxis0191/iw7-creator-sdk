"""Compose tiny ZoneTool source from an existing verified ORIGINAL model writer.

No build, extraction, game launch or runtime installation. Run only after parent
admission permits asset preparation. Refuses an existing output directory.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import manifest


def prepare(writer_run, output):
    # Reuse the measured 24-vertex/12-triangle, material, source pin, LOD and
    # roundtrip gate. Never accept arbitrary H1 bytes through the original probe.
    model_lab = manifest.REPO / "ops/model-lab"
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(model_lab))
        spec = importlib.util.spec_from_file_location("sdk_model_staging", model_lab / "prepare_ff.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        staging = module.stage(Path(writer_run), Path(output))
    finally:
        sys.path[:] = previous
    output = Path(output)
    example = manifest.HERE / "examples/beacon"
    source = (example / "sdk_beacon.gsc").read_bytes()
    data = manifest.load_manifest(example / "manifest.json")
    source_hash = hashlib.sha256(source).hexdigest()
    entry = data["package"]["files"][1]
    entry.update(bytes=len(source), sha256=source_hash)
    data["package"]["closure"]["nodes"][0]["sha256"] = source_hash
    # The new zone name deliberately gets its own generated rawfile. Never
    # relabel the historical FF as a measured build of this gameplay example.
    (output / "zone_source/sdk_beacon.csv").write_bytes((example / "zone.csv").read_bytes())
    (output / "sdk_beacon.gsc").write_bytes(source)
    (output / "manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    report = {"schema": "iw7.beacon-preparation/1", "writer_plan": staging["schema"],
              "zone": "sdk_beacon", "gsc_sha256": source_hash,
              "ff_built": False, "runtime_ready": False,
              "next": "Build zone sdk_beacon under existing admission; inventory, recipient reference and multiplayer tests remain required."}
    (output / "beacon-preparation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--writer-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.writer_run, args.output), indent=2))
