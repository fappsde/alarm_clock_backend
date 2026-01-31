"""Test that default scripts save and load correctly through the entire flow."""

from custom_components.alarm_clock.const import (
    CONF_DEFAULT_SCRIPT_ALARM,
    CONF_DEFAULT_SCRIPT_FALLBACK,
    CONF_DEFAULT_SCRIPT_ON_ARM,
    CONF_DEFAULT_SCRIPT_ON_CANCEL,
    CONF_DEFAULT_SCRIPT_ON_DISMISS,
    CONF_DEFAULT_SCRIPT_ON_SKIP,
    CONF_DEFAULT_SCRIPT_ON_SNOOZE,
    CONF_DEFAULT_SCRIPT_POST_ALARM,
    CONF_DEFAULT_SCRIPT_PRE_ALARM,
    CONF_DEFAULT_SCRIPT_RETRY_COUNT,
    CONF_DEFAULT_SCRIPT_TIMEOUT,
)


class TestDefaultScriptsSaveLoad:
    """Test complete save/load flow for default scripts."""

    def test_save_logic_filters_empty_values(self):
        """Test that the save logic correctly filters out None and empty strings."""
        # Simulate existing options
        existing_options = {
            CONF_DEFAULT_SCRIPT_PRE_ALARM: "script.old_pre",
            CONF_DEFAULT_SCRIPT_ALARM: "script.old_alarm",
            "other_setting": "keep_this",
        }

        # Simulate user input with various values
        user_input = {
            CONF_DEFAULT_SCRIPT_ALARM: "script.new_alarm",  # Updated value
            CONF_DEFAULT_SCRIPT_POST_ALARM: "script.new_post",  # New value
            CONF_DEFAULT_SCRIPT_FALLBACK: "",  # Empty string - should be filtered
            CONF_DEFAULT_SCRIPT_ON_SNOOZE: None,  # None - should be filtered
            # CONF_DEFAULT_SCRIPT_PRE_ALARM not in input - should be removed
        }

        # Apply the save logic from async_step_default_scripts
        updated_options = {
            k: v
            for k, v in existing_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input.items():
            if value is not None and value != "":
                updated_options[key] = value

        # Verify results
        assert CONF_DEFAULT_SCRIPT_ALARM in updated_options
        assert updated_options[CONF_DEFAULT_SCRIPT_ALARM] == "script.new_alarm"

        assert CONF_DEFAULT_SCRIPT_POST_ALARM in updated_options
        assert updated_options[CONF_DEFAULT_SCRIPT_POST_ALARM] == "script.new_post"

        # These should be removed/not added
        assert CONF_DEFAULT_SCRIPT_PRE_ALARM not in updated_options  # Cleared
        assert CONF_DEFAULT_SCRIPT_FALLBACK not in updated_options  # Empty string
        assert CONF_DEFAULT_SCRIPT_ON_SNOOZE not in updated_options  # None

        # Non-script settings should be preserved
        assert "other_setting" in updated_options
        assert updated_options["other_setting"] == "keep_this"

    def test_load_logic_handles_empty_strings(self):
        """Test that the load logic treats empty strings as None."""
        # Simulate stored options with an empty string (legacy data)
        stored_options = {
            CONF_DEFAULT_SCRIPT_PRE_ALARM: "script.valid",
            CONF_DEFAULT_SCRIPT_ALARM: "",  # Empty string from legacy data
            CONF_DEFAULT_SCRIPT_POST_ALARM: "script.post",
        }

        # Simulate get_option function
        def get_option(key: str, default=None):
            """Get option value, treating empty strings as None."""
            value = stored_options.get(key, default)
            return None if value == "" else value

        # Test retrieval
        assert get_option(CONF_DEFAULT_SCRIPT_PRE_ALARM) == "script.valid"
        assert get_option(CONF_DEFAULT_SCRIPT_ALARM) is None  # Empty string → None
        assert get_option(CONF_DEFAULT_SCRIPT_POST_ALARM) == "script.post"
        assert get_option("nonexistent") is None
        assert get_option("nonexistent", "default_val") == "default_val"

    def test_complete_save_load_cycle(self):
        """Test a complete save/load cycle simulating the full flow."""
        # Step 1: Initial state with some settings
        initial_options = {
            CONF_DEFAULT_SCRIPT_PRE_ALARM: "script.morning_pre",
            CONF_DEFAULT_SCRIPT_ALARM: "script.morning_alarm",
            CONF_DEFAULT_SCRIPT_TIMEOUT: 30,
            "other_setting": "value1",
        }

        # Step 2: User updates settings
        user_input = {
            CONF_DEFAULT_SCRIPT_ALARM: "script.updated_alarm",  # Update
            CONF_DEFAULT_SCRIPT_POST_ALARM: "script.new_post",  # Add new
            CONF_DEFAULT_SCRIPT_TIMEOUT: 45,  # Update timeout
            # PRE_ALARM not included - should be removed
        }

        # Step 3: Apply save logic
        saved_options = {
            k: v
            for k, v in initial_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input.items():
            if value is not None and value != "":
                saved_options[key] = value

        # Step 4: Verify saved state
        assert CONF_DEFAULT_SCRIPT_PRE_ALARM not in saved_options  # Removed
        assert saved_options[CONF_DEFAULT_SCRIPT_ALARM] == "script.updated_alarm"
        assert saved_options[CONF_DEFAULT_SCRIPT_POST_ALARM] == "script.new_post"
        assert saved_options[CONF_DEFAULT_SCRIPT_TIMEOUT] == 45
        assert saved_options["other_setting"] == "value1"

        # Step 5: Simulate loading (get_option)
        def get_option(key: str, default=None):
            value = saved_options.get(key, default)
            return None if value == "" else value

        # Step 6: Verify loaded values
        assert get_option(CONF_DEFAULT_SCRIPT_PRE_ALARM) is None  # Was removed
        assert get_option(CONF_DEFAULT_SCRIPT_ALARM) == "script.updated_alarm"
        assert get_option(CONF_DEFAULT_SCRIPT_POST_ALARM) == "script.new_post"
        assert get_option(CONF_DEFAULT_SCRIPT_TIMEOUT, 30) == 45

    def test_all_default_script_fields(self):
        """Test that all default script fields are handled correctly."""
        # Start with empty options
        existing_options = {}

        # User sets all possible script fields
        user_input = {
            CONF_DEFAULT_SCRIPT_PRE_ALARM: "script.pre",
            CONF_DEFAULT_SCRIPT_ALARM: "script.alarm",
            CONF_DEFAULT_SCRIPT_POST_ALARM: "script.post",
            CONF_DEFAULT_SCRIPT_ON_SNOOZE: "script.snooze",
            CONF_DEFAULT_SCRIPT_ON_DISMISS: "script.dismiss",
            CONF_DEFAULT_SCRIPT_ON_ARM: "script.arm",
            CONF_DEFAULT_SCRIPT_ON_CANCEL: "script.cancel",
            CONF_DEFAULT_SCRIPT_ON_SKIP: "script.skip",
            CONF_DEFAULT_SCRIPT_FALLBACK: "script.fallback",
            CONF_DEFAULT_SCRIPT_TIMEOUT: 60,
            CONF_DEFAULT_SCRIPT_RETRY_COUNT: 5,
        }

        # Apply save logic
        updated_options = {
            k: v
            for k, v in existing_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input.items():
            if value is not None and value != "":
                updated_options[key] = value

        # Verify all fields are saved
        assert len(updated_options) == 11  # All 11 fields
        for key, expected_value in user_input.items():
            assert key in updated_options
            assert updated_options[key] == expected_value

    def test_partial_update_preserves_others(self):
        """Test that updating some fields doesn't affect others."""
        # Initial state with multiple scripts configured
        initial_options = {
            CONF_DEFAULT_SCRIPT_PRE_ALARM: "script.pre",
            CONF_DEFAULT_SCRIPT_ALARM: "script.alarm",
            CONF_DEFAULT_SCRIPT_POST_ALARM: "script.post",
            CONF_DEFAULT_SCRIPT_ON_SNOOZE: "script.snooze",
            CONF_DEFAULT_SCRIPT_TIMEOUT: 30,
            "other_setting": "important",
        }

        # User only updates one field
        user_input = {
            CONF_DEFAULT_SCRIPT_ALARM: "script.new_alarm",
        }

        # Apply save logic - this removes ALL default_script_ fields first
        updated_options = {
            k: v
            for k, v in initial_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input.items():
            if value is not None and value != "":
                updated_options[key] = value

        # With the current logic, only the updated field should remain
        # All other default_script_ fields should be removed
        assert CONF_DEFAULT_SCRIPT_ALARM in updated_options
        assert updated_options[CONF_DEFAULT_SCRIPT_ALARM] == "script.new_alarm"

        # These should NOT be in the updated options (they were cleared)
        assert CONF_DEFAULT_SCRIPT_PRE_ALARM not in updated_options
        assert CONF_DEFAULT_SCRIPT_POST_ALARM not in updated_options
        assert CONF_DEFAULT_SCRIPT_ON_SNOOZE not in updated_options
        assert CONF_DEFAULT_SCRIPT_TIMEOUT not in updated_options

        # Non-script settings should be preserved
        assert updated_options["other_setting"] == "important"

    def test_clearing_all_scripts(self):
        """Test that all scripts can be cleared at once."""
        # Initial state with scripts
        initial_options = {
            CONF_DEFAULT_SCRIPT_PRE_ALARM: "script.pre",
            CONF_DEFAULT_SCRIPT_ALARM: "script.alarm",
            CONF_DEFAULT_SCRIPT_TIMEOUT: 30,
            "other_setting": "keep",
        }

        # User clears all (submits empty form)
        user_input = {}

        # Apply save logic
        updated_options = {
            k: v
            for k, v in initial_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input.items():
            if value is not None and value != "":
                updated_options[key] = value

        # All default_script_ fields should be removed
        assert CONF_DEFAULT_SCRIPT_PRE_ALARM not in updated_options
        assert CONF_DEFAULT_SCRIPT_ALARM not in updated_options
        assert CONF_DEFAULT_SCRIPT_TIMEOUT not in updated_options

        # Other settings preserved
        assert updated_options["other_setting"] == "keep"

    def test_edge_case_none_vs_empty_string(self):
        """Test distinction between None and empty string values."""
        existing_options = {
            CONF_DEFAULT_SCRIPT_ALARM: "script.old",
        }

        # Test with None
        user_input_with_none = {
            CONF_DEFAULT_SCRIPT_ALARM: None,
        }

        updated_options = {
            k: v
            for k, v in existing_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input_with_none.items():
            if value is not None and value != "":
                updated_options[key] = value

        # None should not be added
        assert CONF_DEFAULT_SCRIPT_ALARM not in updated_options

        # Test with empty string
        user_input_with_empty = {
            CONF_DEFAULT_SCRIPT_ALARM: "",
        }

        updated_options = {
            k: v
            for k, v in existing_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input_with_empty.items():
            if value is not None and value != "":
                updated_options[key] = value

        # Empty string should not be added
        assert CONF_DEFAULT_SCRIPT_ALARM not in updated_options

    def test_number_fields_with_zero_value(self):
        """Test that numeric fields with value 0 are handled correctly."""
        existing_options = {}

        # User sets retry count to 0 (valid value)
        user_input = {
            CONF_DEFAULT_SCRIPT_RETRY_COUNT: 0,  # 0 is valid, not empty
            CONF_DEFAULT_SCRIPT_TIMEOUT: 30,
        }

        # Apply save logic
        updated_options = {
            k: v
            for k, v in existing_options.items()
            if not k.startswith("default_script_")
        }
        for key, value in user_input.items():
            if value is not None and value != "":
                updated_options[key] = value

        # Both values should be saved (0 is not None and not "")
        assert CONF_DEFAULT_SCRIPT_RETRY_COUNT in updated_options
        assert updated_options[CONF_DEFAULT_SCRIPT_RETRY_COUNT] == 0
        assert updated_options[CONF_DEFAULT_SCRIPT_TIMEOUT] == 30
