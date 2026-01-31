"""Test fallback script bug with device defaults.

This test demonstrates the bug where fallback scripts don't work when
use_device_defaults=True because the code checks alarm.data.script_fallback
directly instead of using _get_effective_script().
"""


def get_effective_script(alarm_data, device_opts, script_attr):
    """Simulates _get_effective_script logic."""
    if not alarm_data["use_device_defaults"]:
        return alarm_data.get(script_attr)
    default_attr = f"default_{script_attr}"
    return device_opts.get(default_attr)


class TestFallbackScriptBug:
    """Test the fallback script bug with device defaults."""

    def test_fallback_script_with_device_defaults(self):
        """Test that fallback script is checked correctly when using device defaults.

        BUG: When use_device_defaults=True, the fallback script check at line 1121
        in coordinator.py fails because it checks alarm.data.script_fallback directly
        instead of using _get_effective_script(alarm, "script_fallback").

        Expected behavior:
        - If use_device_defaults=True and default_script_fallback is set, use it
        - If use_device_defaults=False and script_fallback is set, use it
        - The fallback should trigger when primary script fails
        """
        # Scenario 1: Device defaults enabled with default_script_fallback set
        # In this case, alarm.data.script_fallback is None
        # But device options has default_script_fallback = "script.fallback_device"

        alarm_data_use_defaults = {
            "script_fallback": None,  # Not set on alarm level
            "use_device_defaults": True,
        }

        device_options = {
            "default_script_fallback": "script.fallback_device",
        }

        # Current BUGGY behavior:
        # Line 1121: if alarm.data.script_fallback and script_entity_id != alarm.data.script_fallback:
        # This checks alarm.data.script_fallback which is None
        # So the condition is False and fallback is NOT executed
        buggy_check = alarm_data_use_defaults["script_fallback"] is not None
        assert buggy_check is False, "Buggy code won't execute fallback"

        # Expected CORRECT behavior:
        # Should use _get_effective_script(alarm, "script_fallback")
        # This would return "script.fallback_device" from device_options
        effective_fallback = get_effective_script(
            alarm_data_use_defaults, device_options, "script_fallback"
        )
        assert effective_fallback == "script.fallback_device"
        correct_check = effective_fallback is not None
        assert correct_check is True, "Correct code should execute fallback"

    def test_fallback_script_comparison_bug(self):
        """Test that fallback script comparison is consistent.

        BUG: Line 1121 compares script_entity_id != alarm.data.script_fallback
        But script_entity_id comes from the failed script (via _get_effective_script)
        while alarm.data.script_fallback is the raw value.

        This creates inconsistent comparison when use_device_defaults=True.
        """
        # Scenario: Primary script from device defaults fails
        # script_entity_id = "script.alarm_device" (from default_script_alarm)
        # But comparison uses alarm.data.script_fallback (None)
        # Should compare with effective fallback script

        alarm_data = {
            "script_fallback": None,
            "use_device_defaults": True,
        }

        device_options = {
            "default_script_alarm": "script.alarm_device",
            "default_script_fallback": "script.fallback_device",
        }

        # Simulate failed script execution
        failed_script_entity_id = "script.alarm_device"

        # BUGGY comparison (line 1121)
        # This would compare "script.alarm_device" != None = True
        # But alarm.data.script_fallback is None, so first condition fails
        # (buggy_comparison not used, just illustrating the bug)

        # CORRECT comparison
        effective_fallback = get_effective_script(alarm_data, device_options, "script_fallback")
        correct_comparison = failed_script_entity_id != effective_fallback

        assert effective_fallback == "script.fallback_device"
        assert correct_comparison is True, "Should allow fallback (different script)"

    def test_fallback_prevents_infinite_loop(self):
        """Test that fallback script doesn't call itself (infinite loop prevention)."""
        alarm_data = {
            "script_fallback": "script.same_script",
            "use_device_defaults": False,
        }

        # If the fallback script itself fails, don't call it again
        failed_script_entity_id = "script.same_script"

        effective_fallback = alarm_data["script_fallback"]
        should_execute_fallback = (
            effective_fallback is not None
            and failed_script_entity_id != effective_fallback
        )

        assert should_execute_fallback is False, "Should prevent infinite loop"
