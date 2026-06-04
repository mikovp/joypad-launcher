"""Epic Games manifest JSON parsing helpers."""

import os


def epic_resolve_exe(install_location, data):
    install_location = os.path.normpath(install_location.replace("/", os.sep))
    launch_exe = (
        data.get("LaunchExecutable")
        or data.get("LaunchExecutablePath")
        or data.get("Executable")
    )
    if launch_exe:
        exe_path = os.path.normpath(os.path.join(install_location, launch_exe.replace("/", os.sep)))
        if os.path.isfile(exe_path):
            return exe_path
    launch_cmd = (data.get("LaunchCommand") or "").strip()
    if launch_cmd:
        for name in (launch_cmd, launch_cmd + ".exe"):
            exe_path = os.path.join(install_location, name.replace("/", os.sep))
            if os.path.isfile(exe_path):
                return os.path.normpath(exe_path)
    return None


def epic_image_url(data):
    if not isinstance(data, dict):
        return None
    for key in (
        "ImageUrl",
        "ImageURI",
        "TitleImage",
        "Thumbnail",
        "LandscapeImage",
        "MasterImage",
        "IconUrl",
        "Icon",
        "Image",
    ):
        val = data.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val.strip()
    for nested_key in ("Metadata", "CustomMetadata", "AppInstallationInfo"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            url = epic_image_url(nested)
            if url:
                return url
    return None


def epic_is_playable(data):
    if data.get("bIsIncompleteInstall"):
        return False
    if data.get("bIsExecutable") is False:
        return False
    categories = data.get("AppCategories") or []
    if categories and "games" not in [str(c).lower() for c in categories]:
        if "applications" in [str(c).lower() for c in categories]:
            return False
    technical = (data.get("TechnicalType") or "").lower()
    if technical and "games" not in technical and "applications" in technical:
        return False
    return True
