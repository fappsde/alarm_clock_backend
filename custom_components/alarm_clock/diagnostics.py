"""Diagnostics support for Alarm Clock."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

TO_REDACT = {
    "script_pre_alarm",
    "script_alarm",
    "script_post_alarm",
    "script_on_snooze",
    "script_on_dismiss",
    "script_on_arm",
    "script_on_cancel",
    "script_on_skip",
    "script_fallback",
    "default_script_pre_alarm",
    "default_script_alarm",
    "default_script_post_alarm",
    "default_script_on_snooze",
    "default_script_on_dismiss",
    "default_script_on_arm",
    "default_script_on_cancel",
    "default_script_on_skip",
    "default_script_fallback",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN].get(entry.entry_id)

    if not coordinator:
        return {"error": "Coordinator not found"}

    alarms_data = []
    for alarm_id, alarm in coordinator.alarms.items():
        # Get both raw alarm scripts and effective scripts
        effective_scripts = coordinator.get_alarm_scripts_info(alarm)
        
        alarm_info = {
            "alarm_id": alarm_id,
            "name": alarm.data.name,
            "time": alarm.data.time,
            "enabled": alarm.data.enabled,
            "days": alarm.data.days,
            "one_time": alarm.data.one_time,
            "skip_next": alarm.data.skip_next,
            "snooze_duration": alarm.data.snooze_duration,
            "max_snooze_count": alarm.data.max_snooze_count,
            "auto_dismiss_timeout": alarm.data.auto_dismiss_timeout,
            "pre_alarm_duration": alarm.data.pre_alarm_duration,
            "state": alarm.state.value,
            "snooze_count": alarm.snooze_count,
            "next_trigger": (alarm.next_trigger.isoformat() if alarm.next_trigger else None),
            "last_triggered": (alarm.last_triggered.isoformat() if alarm.last_triggered else None),
            "use_device_defaults": alarm.data.use_device_defaults,
            # Raw alarm-level scripts (may be None if using device defaults)
            "scripts_raw": async_redact_data(
                {
                    "script_pre_alarm": alarm.data.script_pre_alarm,
                    "script_alarm": alarm.data.script_alarm,
                    "script_post_alarm": alarm.data.script_post_alarm,
                    "script_on_snooze": alarm.data.script_on_snooze,
                    "script_on_dismiss": alarm.data.script_on_dismiss,
                    "script_on_arm": alarm.data.script_on_arm,
                    "script_on_cancel": alarm.data.script_on_cancel,
                    "script_on_skip": alarm.data.script_on_skip,
                    "script_fallback": alarm.data.script_fallback,
                },
                TO_REDACT,
            ),
            # Effective scripts (device defaults applied if use_device_defaults=True)
            "scripts_effective": async_redact_data(
                {
                    "script_pre_alarm": effective_scripts.get("script_pre_alarm"),
                    "script_alarm": effective_scripts.get("script_alarm"),
                    "script_post_alarm": effective_scripts.get("script_post_alarm"),
                    "script_on_snooze": effective_scripts.get("script_on_snooze"),
                    "script_on_dismiss": effective_scripts.get("script_on_dismiss"),
                    "script_on_arm": effective_scripts.get("script_on_arm"),
                    "script_on_cancel": effective_scripts.get("script_on_cancel"),
                    "script_on_skip": effective_scripts.get("script_on_skip"),
                    "script_fallback": effective_scripts.get("script_fallback"),
                    "script_timeout": effective_scripts.get("script_timeout"),
                    "script_retry_count": effective_scripts.get("script_retry_count"),
                },
                TO_REDACT,
            ),
        }
        alarms_data.append(alarm_info)

    # Include device-level default scripts from options
    default_scripts = {
        k: v for k, v in entry.options.items() if k.startswith("default_script_")
    }

    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "version": entry.version,
        "default_scripts": async_redact_data(default_scripts, TO_REDACT),
        "alarms": alarms_data,
        "health_status": coordinator.health_status,
        "scheduled_callbacks": list(coordinator._scheduled_callbacks.keys()),
        "snooze_callbacks": list(coordinator._snooze_callbacks.keys()),
        "auto_dismiss_callbacks": list(coordinator._auto_dismiss_callbacks.keys()),
    }
