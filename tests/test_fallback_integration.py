"""Integration test for fallback script with device defaults.

This test validates that the fallback script bug fix works correctly
in a realistic scenario.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.alarm_clock.coordinator import AlarmClockCoordinator
from custom_components.alarm_clock.state_machine import AlarmData, AlarmStateMachine


@pytest.mark.asyncio
async def test_fallback_script_with_device_defaults_integration():
    """Integration test for fallback script execution with device defaults.

    This test verifies:
    1. When use_device_defaults=True and default_script_fallback is set
    2. If primary script fails, the fallback script is executed
    3. The effective fallback script is retrieved correctly
    """
    # Setup mock Home Assistant instance
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}

    # Mock config entry with device defaults
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_id"
    config_entry.options = {
        "default_script_alarm": "script.alarm_device",
        "default_script_fallback": "script.fallback_device",
        "default_script_timeout": 30,
        "default_script_retry_count": 1,  # Only 1 retry for fast test
    }

    # Create coordinator
    with patch("custom_components.alarm_clock.coordinator.AlarmClockStore"):
        coordinator = AlarmClockCoordinator(hass, config_entry)

        # Create an alarm with use_device_defaults=True
        alarm_data = AlarmData(
            alarm_id="test_alarm",
            name="Test Alarm",
            time="07:00",
            use_device_defaults=True,  # Using device defaults
            script_fallback=None,  # No alarm-level fallback
        )

        alarm = AlarmStateMachine(alarm_data, hass)
        coordinator._alarms = {"test_alarm": alarm}

        # Track script execution calls
        script_calls = []

        async def mock_service_call(domain, service, data, blocking):
            """Mock service call that fails for primary script."""
            script_entity = f"script.{service}"
            script_calls.append(script_entity)

            # Fail for the primary alarm script, succeed for fallback
            if script_entity == "script.alarm_device":
                raise Exception("Primary script failed")
            # Fallback script succeeds (returns normally)

        hass.services = MagicMock()
        hass.services.async_call = AsyncMock(side_effect=mock_service_call)

        # Mock event firing
        coordinator._fire_event = MagicMock()

        # Test: Execute the primary script which will fail
        result = await coordinator._async_execute_script(
            "test_alarm",
            "script.alarm_device",
            "alarm"
        )

        # Verify:
        # 1. Primary script was attempted
        assert "script.alarm_device" in script_calls

        # 2. Fallback script was executed (device default)
        assert "script.fallback_device" in script_calls

        # 3. The overall execution succeeded due to fallback
        assert result is True, "Fallback should have succeeded"

        # 4. Script failed event was fired
        coordinator._fire_event.assert_called_once()
        event_type = coordinator._fire_event.call_args[0][0]
        assert "SCRIPT_FAILED" in str(event_type)


@pytest.mark.asyncio
async def test_fallback_script_without_device_defaults_integration():
    """Test fallback script with alarm-level override (use_device_defaults=False)."""
    # Setup mock Home Assistant instance
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}

    # Mock config entry with device defaults
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_id"
    config_entry.options = {
        "default_script_alarm": "script.alarm_device",
        "default_script_fallback": "script.fallback_device",
        "default_script_timeout": 30,
        "default_script_retry_count": 1,
    }

    # Create coordinator
    with patch("custom_components.alarm_clock.coordinator.AlarmClockStore"):
        coordinator = AlarmClockCoordinator(hass, config_entry)

        # Create an alarm with use_device_defaults=False
        alarm_data = AlarmData(
            alarm_id="test_alarm",
            name="Test Alarm",
            time="07:00",
            use_device_defaults=False,  # Using alarm-level scripts
            script_alarm="script.alarm_custom",
            script_fallback="script.fallback_custom",
            script_timeout=30,
            script_retry_count=1,
        )

        alarm = AlarmStateMachine(alarm_data, hass)
        coordinator._alarms = {"test_alarm": alarm}

        # Track script execution calls
        script_calls = []

        async def mock_service_call(domain, service, data, blocking):
            """Mock service call that fails for primary script."""
            script_entity = f"script.{service}"
            script_calls.append(script_entity)

            # Fail for the custom alarm script, succeed for custom fallback
            if script_entity == "script.alarm_custom":
                raise Exception("Primary script failed")
            # Custom fallback script succeeds

        hass.services = MagicMock()
        hass.services.async_call = AsyncMock(side_effect=mock_service_call)

        # Mock event firing
        coordinator._fire_event = MagicMock()

        # Test: Execute the primary script which will fail
        result = await coordinator._async_execute_script(
            "test_alarm",
            "script.alarm_custom",
            "alarm"
        )

        # Verify:
        # 1. Custom primary script was attempted
        assert "script.alarm_custom" in script_calls

        # 2. Custom fallback script was executed (not device default)
        assert "script.fallback_custom" in script_calls

        # 3. Device default fallback was NOT used
        assert "script.fallback_device" not in script_calls

        # 4. The overall execution succeeded due to fallback
        assert result is True, "Fallback should have succeeded"


@pytest.mark.asyncio
async def test_no_fallback_available():
    """Test behavior when no fallback script is available."""
    # Setup mock Home Assistant instance
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}

    # Mock config entry without fallback
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_id"
    config_entry.options = {
        "default_script_alarm": "script.alarm_device",
        # No default_script_fallback
        "default_script_timeout": 30,
        "default_script_retry_count": 1,
    }

    # Create coordinator
    with patch("custom_components.alarm_clock.coordinator.AlarmClockStore"):
        coordinator = AlarmClockCoordinator(hass, config_entry)

        # Create an alarm with use_device_defaults=True, no fallback
        alarm_data = AlarmData(
            alarm_id="test_alarm",
            name="Test Alarm",
            time="07:00",
            use_device_defaults=True,
            script_fallback=None,
        )

        alarm = AlarmStateMachine(alarm_data, hass)
        coordinator._alarms = {"test_alarm": alarm}

        # Mock service call that fails
        async def mock_service_call(domain, service, data, blocking):
            raise Exception("Script failed")

        hass.services = MagicMock()
        hass.services.async_call = AsyncMock(side_effect=mock_service_call)

        # Mock event firing
        coordinator._fire_event = MagicMock()

        # Test: Execute script which will fail
        result = await coordinator._async_execute_script(
            "test_alarm",
            "script.alarm_device",
            "alarm"
        )

        # Verify:
        # 1. The overall execution failed (no fallback available)
        assert result is False, "Should fail when no fallback available"

        # 2. Script failed event was fired
        coordinator._fire_event.assert_called_once()
