"""Tests for edit_error_recovery.py.

These tests ensure the Edit error recovery hook correctly:
1. Detects all known Edit tool failure patterns
2. Handles case variations in error messages
3. Avoids false positives on successful edits or unrelated errors
4. Works with real-world error messages from Claude Code
"""

import pytest

from edit_error_recovery import ERROR_PATTERNS, has_edit_error


class TestHasEditError:
    """Tests for the has_edit_error function.

    This function is the core detection logic for Edit tool failures.
    """

    # =========================================================================
    # Core pattern detection
    # =========================================================================

    def test_detects_old_string_not_found(self):
        """Should detect 'old_string not found' error."""
        assert has_edit_error("old_string not found") is True

    def test_detects_old_string_found_multiple_times(self):
        """Should detect 'old_string found multiple times' error."""
        assert has_edit_error("old_string found multiple times") is True

    def test_detects_old_string_new_string_must_be_different(self):
        """Should detect 'old_string and new_string must be different' error."""
        assert has_edit_error("old_string and new_string must be different") is True

    # =========================================================================
    # Case insensitivity
    # =========================================================================

    @pytest.mark.parametrize(
        "error_text",
        [
            "OLD_STRING NOT FOUND",
            "Old_String Not Found",
            "OLD_STRING not found",
            "old_string NOT FOUND",
        ],
    )
    def test_case_insensitive_not_found(self, error_text):
        """Pattern should match regardless of case."""
        assert has_edit_error(error_text) is True

    @pytest.mark.parametrize(
        "error_text",
        [
            "OLD_STRING FOUND MULTIPLE TIMES",
            "Old_String Found Multiple Times",
            "old_STRING found MULTIPLE times",
        ],
    )
    def test_case_insensitive_multiple_times(self, error_text):
        """Multiple times pattern should match regardless of case."""
        assert has_edit_error(error_text) is True

    @pytest.mark.parametrize(
        "error_text",
        [
            "OLD_STRING AND NEW_STRING MUST BE DIFFERENT",
            "Old_String And New_String Must Be Different",
        ],
    )
    def test_case_insensitive_must_be_different(self, error_text):
        """Must be different pattern should match regardless of case."""
        assert has_edit_error(error_text) is True

    # =========================================================================
    # Real-world error messages from Claude Code
    # =========================================================================

    def test_real_error_not_found_in_content(self):
        """Real Claude Code error: old_string not found in content."""
        real_error = "old_string not found in content"
        assert has_edit_error(real_error) is True

    def test_real_error_multiple_times_with_context(self):
        """Real Claude Code error: multiple times with context suggestion."""
        real_error = (
            "old_string found multiple times and requires more code context "
            "to uniquely identify the intended match"
        )
        assert has_edit_error(real_error) is True

    def test_real_error_with_file_info(self):
        """Error message that includes file path context."""
        error_with_context = (
            "Error editing /path/to/file.py: old_string not found in content. "
            "The file may have changed since you last read it."
        )
        assert has_edit_error(error_with_context) is True

    def test_real_error_json_format(self):
        """Error message that might come in JSON-like format."""
        json_error = '{"error": "old_string not found", "file": "test.py"}'
        assert has_edit_error(json_error) is True

    # =========================================================================
    # Patterns embedded in larger messages
    # =========================================================================

    def test_error_at_start_of_message(self):
        """Error pattern at the start of a longer message."""
        message = "old_string not found. Please re-read the file and try again."
        assert has_edit_error(message) is True

    def test_error_at_end_of_message(self):
        """Error pattern at the end of a longer message."""
        message = "The edit operation failed because old_string not found"
        assert has_edit_error(message) is True

    def test_error_in_middle_of_message(self):
        """Error pattern in the middle of a longer message."""
        message = (
            "Failed to apply edit: old_string found multiple times "
            "in the target file. Please provide more context."
        )
        assert has_edit_error(message) is True

    def test_multiline_message_with_error(self):
        """Error pattern in a multiline message."""
        message = """Edit operation result:
        Status: Failed
        Reason: old_string not found in content
        Suggestion: Re-read the file before editing"""
        assert has_edit_error(message) is True

    # =========================================================================
    # Successful edits - should NOT trigger
    # =========================================================================

    def test_successful_edit_no_trigger(self):
        """Successful edit messages should not trigger error detection."""
        success_messages = [
            "Edit successful",
            "File edited successfully",
            "Changes applied to /path/to/file.py",
            "1 line changed",
            "Edit completed: replaced 'foo' with 'bar'",
        ]
        for message in success_messages:
            assert has_edit_error(message) is False, f"False positive on: {message}"

    def test_empty_string_no_trigger(self):
        """Empty string should not trigger error detection."""
        assert has_edit_error("") is False

    def test_whitespace_only_no_trigger(self):
        """Whitespace-only string should not trigger."""
        assert has_edit_error("   \n\t  ") is False

    # =========================================================================
    # Avoiding false positives - similar but non-matching text
    # =========================================================================

    def test_partial_match_old_string_alone(self):
        """Just 'old_string' without the error context should not match."""
        # This tests that we don't match on partial patterns
        assert has_edit_error("old_string") is False

    def test_partial_match_not_found_alone(self):
        """Just 'not found' without old_string should not match."""
        assert has_edit_error("File not found") is False
        assert has_edit_error("Variable not found") is False

    def test_partial_match_multiple_times_alone(self):
        """Just 'multiple times' without old_string should not match."""
        assert has_edit_error("Called multiple times") is False
        assert has_edit_error("Appears multiple times in the document") is False

    def test_similar_but_different_wording(self):
        """Similar but differently worded messages should not match."""
        non_matching = [
            "old string not found",  # Missing underscore
            "oldstring not found",  # Missing underscore
            "old_string wasn't found",  # Different verb
            "old_string is not found",  # Extra word
            "the old_string cannot be found",  # Different phrasing
            "new_string not found",  # Wrong variable name
        ]
        for message in non_matching:
            assert has_edit_error(message) is False, f"False positive on: {message}"

    def test_unrelated_errors(self):
        """Completely unrelated error messages should not match."""
        unrelated = [
            "Permission denied",
            "File is read-only",
            "Syntax error in file",
            "Network timeout",
            "Invalid JSON format",
            "TypeError: cannot read property 'x' of undefined",
        ]
        for message in unrelated:
            assert has_edit_error(message) is False, f"False positive on: {message}"

    # =========================================================================
    # Edge cases
    # =========================================================================

    def test_unicode_in_message(self):
        """Messages with unicode should still match patterns."""
        message = "Error: old_string not found in file containing emoji"
        assert has_edit_error(message) is True

    def test_very_long_message(self):
        """Very long messages should still be searched correctly."""
        padding = "x" * 10000
        message = f"{padding} old_string not found {padding}"
        assert has_edit_error(message) is True

    def test_special_regex_characters_in_context(self):
        """Special regex characters in surrounding text shouldn't break matching."""
        message = "File: test.py (line 42) [error] old_string not found *.txt"
        assert has_edit_error(message) is True


class TestErrorPatterns:
    """Tests for the ERROR_PATTERNS constant.

    These tests verify the patterns themselves are correctly defined.
    """

    def test_three_patterns_defined(self):
        """Should have exactly three error patterns."""
        assert len(ERROR_PATTERNS) == 3

    def test_all_patterns_are_compiled(self):
        """All patterns should be compiled regex objects."""
        import re

        for pattern in ERROR_PATTERNS:
            assert isinstance(pattern, re.Pattern)

    def test_all_patterns_are_case_insensitive(self):
        """All patterns should have IGNORECASE flag."""
        import re

        for pattern in ERROR_PATTERNS:
            assert pattern.flags & re.IGNORECASE


class TestRealWorldScenarios:
    """Integration-style tests with realistic error scenarios.

    These test complete error messages as they would appear from Claude Code.
    """

    def test_scenario_file_changed_since_read(self):
        """Scenario: User's file was modified externally."""
        error = (
            "Edit failed for /Users/dev/project/src/main.py:\n"
            "old_string not found in content.\n"
            "The file may have been modified since you last read it. "
            "Please read the file again to get the current content."
        )
        assert has_edit_error(error) is True

    def test_scenario_whitespace_mismatch(self):
        """Scenario: Whitespace/indentation doesn't match."""
        error = (
            "old_string not found in content. "
            "Check for whitespace or indentation differences."
        )
        assert has_edit_error(error) is True

    def test_scenario_ambiguous_match(self):
        """Scenario: Multiple occurrences of the target string."""
        error = (
            "old_string found multiple times and requires more code context "
            "to uniquely identify the intended match. Either provide a larger "
            "string with more surrounding context to make it unique or use "
            "`replaceAll` to change every instance of `oldString`."
        )
        assert has_edit_error(error) is True

    def test_scenario_no_op_edit(self):
        """Scenario: User tried to replace text with itself."""
        error = (
            "old_string and new_string must be different. "
            "The edit would result in no changes to the file."
        )
        assert has_edit_error(error) is True

    def test_scenario_successful_edit(self):
        """Scenario: Edit succeeded - should not trigger."""
        success = (
            "Successfully edited /Users/dev/project/src/main.py:\n"
            "- Replaced 1 occurrence\n"
            "- Lines changed: 45-47"
        )
        assert has_edit_error(success) is False

    def test_scenario_read_tool_error(self):
        """Scenario: Different tool (Read) error - should not trigger."""
        read_error = "Error reading file: /path/to/file.py not found"
        assert has_edit_error(read_error) is False
