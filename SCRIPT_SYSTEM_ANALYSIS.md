# Script System Analysis and Bug Fix Report

## Executive Summary

This document provides an in-depth analysis of the alarm clock script system, including how scripts are saved, managed, loaded, and displayed. The analysis revealed **2 critical bugs** in the fallback script logic that have been fixed.

## Script System Architecture

### Overview

The alarm clock system supports two types of scripts:

1. **Device-Level Default Scripts**: Configured once and applied to all alarms that opt-in
2. **Per-Alarm Custom Scripts**: Override device defaults for specific alarms

### Script Types (9 per alarm)

#### Lifecycle Scripts
- `script_pre_alarm`: Executed N minutes before alarm time
- `script_alarm`: Executed at alarm time (primary alarm script)
- `script_post_alarm`: Executed after dismiss or timeout

#### Event Scripts
- `script_on_snooze`: Executed when user hits snooze
- `script_on_dismiss`: Executed when user dismisses alarm
- `script_on_arm`: Executed when alarm is enabled
- `script_on_cancel`: Executed when alarm is canceled while active
- `script_on_skip`: Executed when skip_next is activated

#### Fallback Script
- `script_fallback`: Executed if any other script fails (with retry logic)

## How Scripts Are Saved

### Device-Level Default Scripts

**Storage Location**: `ConfigEntry.options`

**Keys**: Prefixed with `default_script_*`
```python
{
    "default_script_pre_alarm": "script.morning_pre",
    "default_script_alarm": "script.morning_alarm",
    "default_script_post_alarm": "script.morning_post",
    "default_script_on_snooze": "script.snooze_action",
    "default_script_on_dismiss": "script.dismiss_action",
    "default_script_on_arm": "script.arm_action",
    "default_script_on_cancel": "script.cancel_action",
    "default_script_on_skip": "script.skip_action",
    "default_script_fallback": "script.fallback",
    "default_script_timeout": 30,
    "default_script_retry_count": 3
}
```

**Configuration Flow**: `config_flow.py::async_step_default_scripts()`
- Uses `EntitySelector` to list available scripts
- Properly removes cleared fields when saving
- Updates via `hass.config_entries.async_update_entry()`

### Per-Alarm Custom Scripts

**Storage Location**: `.storage/alarm_clock.storage_{entry_id}` (JSON file)

**Data Structure**: Part of `AlarmData` dataclass
```python
{
    "alarm_id": "alarm_abc123",
    "name": "Morning Alarm",
    "time": "07:00",
    "use_device_defaults": true,  # Toggle flag
    "script_pre_alarm": null,     # Alarm-level overrides
    "script_alarm": null,
    "script_post_alarm": null,
    "script_on_snooze": null,
    "script_on_dismiss": null,
    "script_on_arm": null,
    "script_on_cancel": null,
    "script_on_skip": null,
    "script_fallback": null,
    "script_timeout": 30,
    "script_retry_count": 3
}
```

**Persistence**: `AlarmClockStore` class
- Async JSON storage via Home Assistant's storage helper
- Loaded on startup in `async_setup_entry()`
- Saved via `store.async_update_alarm(alarm.data)`

## How Scripts Are Managed

### The Toggle: `use_device_defaults`

This boolean flag determines script resolution:

- **`use_device_defaults=True`** (default for new alarms)
  - All scripts come from `ConfigEntry.options` (device defaults)
  - Alarm-level script fields are ignored even if set
  
- **`use_device_defaults=False`**
  - Uses alarm-specific script configuration
  - Automatically set when calling `async_set_scripts()` service

### Effective Script Resolution

**Method**: `_get_effective_script(alarm, script_attr)`

```python
def _get_effective_script(self, alarm: AlarmStateMachine, script_attr: str) -> str | None:
    """Get the effective script for an alarm based on device defaults setting."""
    if not alarm.data.use_device_defaults:
        # Use alarm-specific scripts
        return getattr(alarm.data, script_attr)
    
    # Use device-level defaults from config entry options
    options = self.entry.options
    default_attr = f"default_{script_attr}"
    return options.get(default_attr)
```

**This method is used for:**
- Script execution (lifecycle and event scripts)
- Script information display (attributes)
- Timeout and retry count resolution

## How Scripts Are Loaded

### Startup Sequence

1. **Integration Setup** (`__init__.py::async_setup_entry()`)
   ```python
   coordinator = AlarmClockCoordinator(hass, config_entry)
   store = AlarmClockStore(hass, config_entry.entry_id)
   ```

2. **Storage Load** (`store.py::async_load()`)
   ```python
   data = await self._store.async_load()
   alarms = [AlarmData.from_dict(alarm_dict) for alarm_dict in data["alarms"]]
   ```

3. **State Machine Creation** (`coordinator.py`)
   ```python
   for alarm_data in stored_alarms:
       alarm = AlarmStateMachine(alarm_data, hass)
       self._alarms[alarm_data.alarm_id] = alarm
   ```

4. **Entity Registration**
   - Switch entities (enable/disable)
   - Time entities (alarm time)
   - Sensor entities (state, next trigger)
   - Binary sensor entities (ringing status)

### Configuration Loading

Device defaults are loaded from `config_entry.options` on coordinator initialization:
```python
self.entry = config_entry
# Options are accessed directly: self.entry.options.get("default_script_alarm")
```

## How Scripts Are Shown

### Entity Attributes

Both switch and time entities expose script information via `extra_state_attributes`:

```python
def extra_state_attributes(self) -> dict[str, Any]:
    scripts_info = self.coordinator.get_alarm_scripts_info(alarm)
    return {
        "use_device_defaults": scripts_info["use_device_defaults"],
        "script_pre_alarm": scripts_info["script_pre_alarm"],
        "script_alarm": scripts_info["script_alarm"],
        "script_post_alarm": scripts_info["script_post_alarm"],
        "script_on_snooze": scripts_info["script_on_snooze"],
        "script_on_dismiss": scripts_info["script_on_dismiss"],
        "script_on_arm": scripts_info["script_on_arm"],
        "script_on_cancel": scripts_info["script_on_cancel"],
        "script_on_skip": scripts_info["script_on_skip"],
        "script_fallback": scripts_info["script_fallback"],
        "script_timeout": scripts_info["script_timeout"],
        "script_retry_count": scripts_info["script_retry_count"],
    }
```

**Method**: `get_alarm_scripts_info(alarm)`
- Correctly uses `_get_effective_script()` for all script fields
- Returns the actual script entity IDs that will be executed
- Respects `use_device_defaults` flag

### Home Assistant UI

Scripts are shown in:
1. Entity state attributes (Developer Tools → States)
2. Entity card details
3. Configuration flow (when editing alarm or device defaults)

## Bugs Found and Fixed

### Bug #1: Fallback Script Not Using Effective Resolution

**Location**: `coordinator.py` line 1121

**Problem**:
```python
# OLD BUGGY CODE
if alarm.data.script_fallback and script_entity_id != alarm.data.script_fallback:
```

This directly accessed `alarm.data.script_fallback` instead of using `_get_effective_script()`.

**Impact**:
- When `use_device_defaults=True`, `alarm.data.script_fallback` is `None`
- Even if `default_script_fallback` is configured, fallback never executes
- Users lose error recovery capability when using device defaults

**Fix**:
```python
# NEW FIXED CODE
effective_fallback = self._get_effective_script(alarm, "script_fallback")
if effective_fallback and script_entity_id != effective_fallback:
```

### Bug #2: Inconsistent Fallback Comparison

**Location**: Same line (1121)

**Problem**:
- `script_entity_id` comes from effective script resolution (respects device defaults)
- But compared against raw `alarm.data.script_fallback` (doesn't respect device defaults)
- Inconsistent data sources for comparison

**Impact**:
- Fallback might not execute when it should
- Or might try to execute when the fallback itself failed (infinite loop risk)

**Fix**:
- Use `effective_fallback` for both existence check and comparison
- Ensures consistent script resolution logic

## Testing

### Unit Tests (`test_fallback_script_bug.py`)

Documents the bug with clear before/after examples:
- `test_fallback_script_with_device_defaults`: Demonstrates the primary bug
- `test_fallback_script_comparison_bug`: Shows inconsistent comparison
- `test_fallback_prevents_infinite_loop`: Validates loop prevention

### Integration Tests (`test_fallback_integration.py`)

Comprehensive scenarios:
- Fallback with device defaults (the bug scenario)
- Fallback with alarm-level overrides
- No fallback available (failure case)

All tests use mocked Home Assistant services to validate behavior.

## Validation

✅ **Linting**: All files pass `ruff` checks
✅ **Security**: CodeQL analysis found no vulnerabilities
✅ **Code Review**: Addressed feedback on code duplication
✅ **Testing**: Created comprehensive test coverage

## Conclusion

The script system architecture is well-designed with:
- Clear separation between device defaults and alarm overrides
- Consistent use of `_get_effective_script()` throughout (except for the bug)
- Proper persistence and loading mechanisms
- Good UI exposure of script configuration

The fallback script bug was a critical oversight that prevented proper error recovery when using device defaults. The fix ensures that all script resolution paths use the same logic, maintaining consistency across the system.

## Recommendations

1. ✅ **Immediate**: Apply the bug fix (completed)
2. ✅ **Short-term**: Add integration tests (completed)
3. 🔄 **Medium-term**: Consider adding validation to prevent direct access to `alarm.data.script_*` fields outside of setters
4. 🔄 **Long-term**: Add monitoring/telemetry for script failures to detect issues in production

---

**Analysis Date**: 2026-01-31
**Fixed in PR**: copilot/analyze-script-system-management
**Files Changed**: 
- `custom_components/alarm_clock/coordinator.py` (bug fix)
- `tests/test_fallback_script_bug.py` (unit tests)
- `tests/test_fallback_integration.py` (integration tests)
