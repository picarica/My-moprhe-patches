#!/usr/bin/env python3
import json
import re
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parent.parent
properties = (root / "gradle.properties").read_text(encoding="utf-8")
version_match = re.search(r"^version = (.+)$", properties, re.MULTILINE)
if version_match is None:
    raise SystemExit("gradle.properties has no version")
version = version_match.group(1)

bundle = json.loads((root / "patches-bundle.json").read_text(encoding="utf-8"))
patch_list = json.loads((root / "patches-list.json").read_text(encoding="utf-8"))
mpp = root / "patches" / "build" / "libs" / f"patches-{version}.mpp"
changelog = root / "CHANGELOG.md"

expected_url = (
    "https://github.com/picarica/My-moprhe-patches/releases/download/"
    f"v{version}/patches-{version}.mpp"
)

assert bundle["version"] == version, "patches-bundle.json version is stale"
assert bundle["download_url"] == expected_url, "patches-bundle.json URL is stale"
assert patch_list["version"] == version, "patches-list.json version is stale"
assert mpp.is_file() and mpp.stat().st_size > 1_000, f"MPP is missing: {mpp}"
assert changelog.is_file() and f"## [{version}]" in changelog.read_text(encoding="utf-8"), (
    "CHANGELOG.md has no entry for the current version"
)

# Third-party JsonPatchBundle metadata is deserialized by Morphe Manager directly
# into kotlinx.datetime.LocalDateTime. It must not contain Z or a UTC offset.
created_at = bundle["created_at"]
parsed = datetime.fromisoformat(created_at)
assert parsed.tzinfo is None, "created_at must be a timezone-less LocalDateTime"
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", created_at), (
    "created_at must use YYYY-MM-DDTHH:MM:SS"
)

assert len(patch_list["patches"]) == 2, "expected exactly two published patches"
patches = {patch["name"]: patch for patch in patch_list["patches"]}
assert set(patches) == {
    "Remove Google Play requirement",
    "Remove Google requirements",
}

affine = patches["Remove Google requirements"]
affine_compatibility = affine["compatiblePackages"][0]
assert affine_compatibility["packageName"] == "app.affine.pro"
assert affine_compatibility["apkFileType"] == "XAPK_REQUIRED"
assert len(affine_compatibility["signatures"]) == 2
affine_target = affine_compatibility["targets"][0]
assert affine_target["version"] == "0.27.4"
assert affine_target["versionCodes"]["ARM64_V8A"] == 439

stick_war = patches["Remove Google Play requirement"]
stick_war_compatibility = stick_war["compatiblePackages"][0]
assert stick_war_compatibility["packageName"] == "com.maxgames.stickwarlegacy"
assert stick_war_compatibility["apkFileType"] == "XAPK_REQUIRED"
assert stick_war_compatibility["signatures"] == [
    "59bc9becd6fa02f2ff43c6d31aacc93246d8b63e7973494198f15f99e3988666"
]
stick_war_target = stick_war_compatibility["targets"][0]
assert stick_war_target["version"] == "2026.1.983"
assert stick_war_target["versionCodes"]["ARM64_V8A"] == 2026001983

print(f"Release metadata is consistent for v{version}.")
