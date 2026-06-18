# DDC/CI monitor control — https://github.com/thlter/DDCCI_tool (MIT)

import os
import sys
import threading
import time
from datetime import datetime

from .vcp import open_phy_monitors


def settings_from_config(config):
    ddcci = config.get("ddcci")
    if not isinstance(ddcci, dict):
        return False, None, None, False
    enabled = bool(ddcci.get("power_off_on_start"))
    monitors = ddcci.get("monitors")
    if monitors is not None and not isinstance(monitors, (list, tuple)):
        monitors = None
    models = ddcci.get("models")
    if models is not None and not isinstance(models, (list, tuple)):
        models = None
    log_enabled = bool(ddcci.get("log"))
    return enabled, monitors, models, log_enabled


def _delay_seconds(config):
    ddcci = config.get("ddcci") or {}
    try:
        ms = float(ddcci.get("delay_ms", 2000))
        return max(0.0, ms / 1000.0)
    except (TypeError, ValueError):
        return 2.0


def _log(base_dir, lines, enabled=False):
    if not enabled or not base_dir:
        return
    path = os.path.join(base_dir, "ddcci.log")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (stamp, lines[0]))
            for line in lines[1:]:
                f.write("  %s\n" % line)
    except OSError:
        pass


def _match_monitor_label(pm):
    return (pm.model or pm.description or "").strip()


def _select_targets(phy_monitors, monitor_indices=None, monitor_models=None):
    if not phy_monitors:
        return []

    if monitor_models:
        wanted = [str(m).upper() for m in monitor_models]
        return [
            pm for pm in phy_monitors
            if any(w in _match_monitor_label(pm).upper() for w in wanted)
        ]

    if monitor_indices is not None:
        wanted = {int(i) for i in monitor_indices}
        return [pm for i, pm in enumerate(phy_monitors) if i in wanted]

    return phy_monitors


def power_off_monitors(
    monitor_indices=None,
    monitor_models=None,
    base_dir=None,
    tag="",
    log_enabled=False,
):
    """Power off monitor(s) via DDC/CI. No-op outside Windows."""
    lines = ["%s start" % (tag or "power_off")]
    if sys.platform != "win32":
        lines.append("skip: not win32")
        _log(base_dir, lines, log_enabled)
        return False

    ok_any = False
    phy_monitors = []
    try:
        phy_monitors = open_phy_monitors()
        lines.append("found %d DDC/CI monitor(s)" % len(phy_monitors))
        for i, pm in enumerate(phy_monitors):
            lines.append("[%d] model=%r desc=%r" % (i, pm.model, pm.description))

        targets = _select_targets(phy_monitors, monitor_indices, monitor_models)
        lines.append("targets: %d" % len(targets))
        if not targets:
            lines.append("nothing to do")
            _log(base_dir, lines, log_enabled)
            return False

        for pm in targets:
            label = _match_monitor_label(pm) or pm.description or "monitor"
            ok = pm.power_off()
            lines.append("power_off %r -> %s" % (label, ok))
            ok_any = ok_any or ok
            time.sleep(0.2)
    except Exception as err:
        lines.append("ERROR: %s" % err)
    finally:
        for pm in phy_monitors:
            try:
                pm.close()
            except Exception:
                pass

    lines.append("result: %s" % ("ok" if ok_any else "failed"))
    _log(base_dir, lines, log_enabled)
    return ok_any


def apply_startup_from_config(config, base_dir=None, force=False):
    """Power off once immediately (before heavy launcher init)."""
    enabled, monitors, models, log_enabled = settings_from_config(config)
    if enabled or force:
        power_off_monitors(
            monitors, models, base_dir, tag="immediate", log_enabled=log_enabled
        )


def schedule_delayed_power_off(config, base_dir=None, force=False):
    """Power off again after delay — pygame flip often wakes the panel."""
    enabled, monitors, models, log_enabled = settings_from_config(config)
    if not enabled and not force:
        return

    delay = _delay_seconds(config)

    def _job():
        if delay > 0:
            time.sleep(delay)
        power_off_monitors(
            monitors, models, base_dir, tag="delayed", log_enabled=log_enabled
        )

    threading.Thread(target=_job, daemon=True).start()


def power_off_from_config(config, base_dir=None):
    """Power off monitors once using ddcci monitor/log settings from config."""
    _, monitors, models, log_enabled = settings_from_config(config)
    return power_off_monitors(
        monitors, models, base_dir, tag="cli", log_enabled=log_enabled
    )
