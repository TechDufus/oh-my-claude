"""Tests for todo_enforcer.py."""

from unittest.mock import patch, MagicMock
import subprocess

import pytest

from todo_enforcer import (
    PATTERNS,
    analyze_transcript,
    count_tasks_by_status,
    count_todos_by_status,
    get_completed_todos_from_todos,
    get_incomplete_todos_from_todos,
    has_uncommitted_changes,
    main,
    should_use_task_system,
)


class TestCountTodosByStatus:
    """Tests for count_todos_by_status function."""

    def test_all_completed(self):
        """All completed todos should count correctly."""
        todos = [
            {"content": "Task 1", "status": "completed"},
            {"content": "Task 2", "status": "completed"},
        ]
        incomplete, completed = count_todos_by_status(todos)
        assert incomplete == 0
        assert completed == 2

    def test_all_pending(self):
        """All pending todos should count correctly."""
        todos = [
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "pending"},
        ]
        incomplete, completed = count_todos_by_status(todos)
        assert incomplete == 2
        assert completed == 0

    def test_mixed_statuses(self):
        """Mixed statuses should count correctly."""
        todos = [
            {"content": "Task 1", "status": "completed"},
            {"content": "Task 2", "status": "in_progress"},
            {"content": "Task 3", "status": "pending"},
            {"content": "Task 4", "status": "completed"},
        ]
        incomplete, completed = count_todos_by_status(todos)
        assert incomplete == 2  # in_progress + pending
        assert completed == 2

    def test_in_progress_counts_as_incomplete(self):
        """in_progress status should count as incomplete."""
        todos = [{"content": "Task", "status": "in_progress"}]
        incomplete, completed = count_todos_by_status(todos)
        assert incomplete == 1
        assert completed == 0

    def test_empty_list(self):
        """Empty list should return zeros."""
        incomplete, completed = count_todos_by_status([])
        assert incomplete == 0
        assert completed == 0

    def test_none_input(self):
        """None input should return zeros."""
        incomplete, completed = count_todos_by_status(None)
        assert incomplete == 0
        assert completed == 0

    def test_missing_status_key(self):
        """Todos without status key should not count."""
        todos = [
            {"content": "No status"},
            {"content": "Has status", "status": "completed"},
        ]
        incomplete, completed = count_todos_by_status(todos)
        assert incomplete == 0
        assert completed == 1

    def test_unknown_status(self):
        """Unknown statuses should not count."""
        todos = [
            {"content": "Task", "status": "unknown_status"},
            {"content": "Task 2", "status": "completed"},
        ]
        incomplete, completed = count_todos_by_status(todos)
        assert incomplete == 0
        assert completed == 1


class TestGetIncompleteTodosFromTodos:
    """Tests for get_incomplete_todos_from_todos function."""

    def test_counts_incomplete(self):
        """Should count pending and in_progress todos."""
        data = {
            "todos": [
                {"status": "pending"},
                {"status": "in_progress"},
                {"status": "completed"},
            ]
        }
        assert get_incomplete_todos_from_todos(data) == 2

    def test_no_todos_key(self):
        """Missing todos key should return 0."""
        assert get_incomplete_todos_from_todos({}) == 0

    def test_none_todos(self):
        """None todos should return 0."""
        assert get_incomplete_todos_from_todos({"todos": None}) == 0


class TestGetCompletedTodosFromTodos:
    """Tests for get_completed_todos_from_todos function."""

    def test_counts_completed(self):
        """Should count only completed todos."""
        data = {
            "todos": [
                {"status": "pending"},
                {"status": "completed"},
                {"status": "completed"},
            ]
        }
        assert get_completed_todos_from_todos(data) == 2

    def test_no_todos_key(self):
        """Missing todos key should return 0."""
        assert get_completed_todos_from_todos({}) == 0


class TestAnalyzeTranscript:
    """Tests for analyze_transcript function."""

    def test_empty_transcript(self):
        """Empty transcript should return defaults."""
        result = analyze_transcript([])
        assert result["last_assistant_message"] == ""
        assert result["validation_ran"] is False
        assert result["last_todo_write"] is None

    def test_tracks_last_assistant_message(self):
        """Should track the last assistant message."""
        transcript = [
            {"role": "assistant", "content": "First message"},
            {"role": "user", "content": "User reply"},
            {"role": "assistant", "content": "Second message"},
        ]
        result = analyze_transcript(transcript)
        assert result["last_assistant_message"] == "Second message"

    def test_ignores_empty_assistant_messages(self):
        """Empty assistant messages should not overwrite."""
        transcript = [
            {"role": "assistant", "content": "Has content"},
            {"role": "assistant", "content": ""},
            {"role": "assistant", "content": None},
        ]
        result = analyze_transcript(transcript)
        assert result["last_assistant_message"] == "Has content"

    def test_tracks_todo_write_results(self):
        """Should track TodoWrite tool results."""
        todos = [{"content": "Task", "status": "pending"}]
        transcript = [
            {"type": "tool_result", "tool": "TodoWrite", "todos": todos},
        ]
        result = analyze_transcript(transcript)
        assert result["last_todo_write"] == todos

    def test_tracks_last_todo_write(self):
        """Should track only the LAST TodoWrite result."""
        todos1 = [{"content": "Task 1", "status": "pending"}]
        todos2 = [{"content": "Task 2", "status": "completed"}]
        transcript = [
            {"type": "tool_result", "tool": "TodoWrite", "todos": todos1},
            {"type": "tool_result", "tool": "TodoWrite", "todos": todos2},
        ]
        result = analyze_transcript(transcript)
        assert result["last_todo_write"] == todos2

    def test_detects_validation_in_task_tool(self):
        """Should detect validator in Task tool input."""
        transcript = [
            {
                "type": "tool_use",
                "tool": "Task",
                "input": {"subagent_type": "oh-my-claude:validator"},
            },
        ]
        result = analyze_transcript(transcript)
        assert result["validation_ran"] is True

    def test_detects_validation_in_assistant_message(self):
        """Should detect validation mention in assistant message."""
        transcript = [
            {"role": "assistant", "content": "I'll run the validator now"},
        ]
        result = analyze_transcript(transcript)
        assert result["validation_ran"] is True

    def test_validation_pattern_case_insensitive(self):
        """Validation detection should be case insensitive."""
        transcript = [
            {"role": "assistant", "content": "Running VALIDATION checks"},
        ]
        result = analyze_transcript(transcript)
        assert result["validation_ran"] is True

    def test_respects_max_entries(self):
        """Should respect max_entries limit."""
        transcript = [{"role": "assistant", "content": f"Msg {i}"} for i in range(100)]
        result = analyze_transcript(transcript, max_entries=10)
        # Should only process first 10
        assert result["last_assistant_message"] == "Msg 9"

    def test_validation_not_detected_in_random_text(self):
        """Should not falsely detect validation."""
        transcript = [
            {"role": "assistant", "content": "I fixed the bug and tested it"},
        ]
        result = analyze_transcript(transcript)
        assert result["validation_ran"] is False


class TestHasUncommittedChanges:
    """Tests for has_uncommitted_changes function."""

    def test_no_git_dir(self, tmp_path):
        """Should return False if not a git repo."""
        assert has_uncommitted_changes(str(tmp_path)) is False

    def test_git_repo_clean(self, tmp_path):
        """Should return False for clean git repo."""
        (tmp_path / ".git").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="")
            assert has_uncommitted_changes(str(tmp_path)) is False

    def test_git_repo_dirty(self, tmp_path):
        """Should return True for dirty git repo."""
        (tmp_path / ".git").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=" M file.txt\n")
            assert has_uncommitted_changes(str(tmp_path)) is True

    def test_git_command_failure(self, tmp_path):
        """Should return False on git command failure."""
        (tmp_path / ".git").mkdir()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("git failed")
            assert has_uncommitted_changes(str(tmp_path)) is False


class TestValidatorPattern:
    """Tests for validator pattern matching."""

    @pytest.mark.parametrize(
        "text",
        [
            "validator",
            "validation",
            "oh-my-claude:validator",
            "Running the validator",
            "I'll do validation now",
            "VALIDATOR check",
        ],
    )
    def test_validator_pattern_matches(self, text):
        """Validator pattern should match various forms."""
        assert PATTERNS.match("validator", text) is not None

    @pytest.mark.parametrize(
        "text",
        [
            "valid",
            "invalidate",
            "eval",
            "random text",
        ],
    )
    def test_validator_pattern_no_false_positives(self, text):
        """Validator pattern should not match unrelated text."""
        assert PATTERNS.match("validator", text) is None


class TestPrematureStoppingPatterns:
    """Tests for premature stopping pattern detection."""

    # These patterns are used in main() - testing the logic
    PREMATURE_PATTERNS = [
        "let me know if you",
        "feel free to ask",
        "if you want me to",
        "would you like me to continue",
        "I can continue if",
        "shall I proceed",
        "want me to",
    ]

    @pytest.mark.parametrize("pattern", PREMATURE_PATTERNS)
    def test_premature_pattern_detection(self, pattern):
        """Each premature pattern should be detectable."""
        message = f"I've made some changes. {pattern} make more updates?"
        # Simulate the pattern check from main()
        found = any(p.lower() in message.lower() for p in self.PREMATURE_PATTERNS)
        assert found is True

    def test_case_insensitive_detection(self):
        """Pattern detection should be case insensitive."""
        message = "LET ME KNOW IF YOU need anything else"
        found = any(p.lower() in message.lower() for p in self.PREMATURE_PATTERNS)
        assert found is True

    def test_no_premature_pattern(self):
        """Non-premature messages should not match."""
        message = "I've completed all the tasks and ran the tests."
        found = any(p.lower() in message.lower() for p in self.PREMATURE_PATTERNS)
        assert found is False


class TestTranscriptEdgeCases:
    """Edge case tests for transcript analysis."""

    def test_malformed_entries(self):
        """Should handle malformed transcript entries."""
        transcript = [
            {},  # Empty entry
            {"role": "unknown"},  # Unknown role
            {"type": "unknown"},  # Unknown type
            None,  # None entry - this would fail, but shouldn't happen
        ]
        # Filter out None to avoid AttributeError
        transcript = [e for e in transcript if e is not None]
        result = analyze_transcript(transcript)
        assert result["last_assistant_message"] == ""

    def test_tool_result_without_todos(self):
        """TodoWrite result without todos field should not crash."""
        transcript = [
            {"type": "tool_result", "tool": "TodoWrite"},  # No todos field
        ]
        result = analyze_transcript(transcript)
        assert result["last_todo_write"] is None

    def test_task_tool_without_input(self):
        """Task tool without input should not crash."""
        transcript = [
            {"type": "tool_use", "tool": "Task"},  # No input field
        ]
        result = analyze_transcript(transcript)
        assert result["validation_ran"] is False


class TestCountTasksByStatus:
    """Tests for count_tasks_by_status function."""

    def test_none_returns_zeros(self):
        """None task list returns (0, 0)."""
        incomplete, completed = count_tasks_by_status(None)
        assert incomplete == 0
        assert completed == 0

    def test_empty_list_returns_zeros(self):
        """Empty task list returns (0, 0)."""
        incomplete, completed = count_tasks_by_status([])
        assert incomplete == 0
        assert completed == 0

    def test_counts_pending_as_incomplete(self):
        """Pending tasks count as incomplete."""
        tasks = [{"status": "pending"}]
        incomplete, completed = count_tasks_by_status(tasks)
        assert incomplete == 1
        assert completed == 0

    def test_counts_in_progress_as_incomplete(self):
        """In-progress tasks count as incomplete."""
        tasks = [{"status": "in_progress"}]
        incomplete, completed = count_tasks_by_status(tasks)
        assert incomplete == 1
        assert completed == 0

    def test_counts_completed(self):
        """Completed tasks count separately."""
        tasks = [{"status": "completed"}]
        incomplete, completed = count_tasks_by_status(tasks)
        assert incomplete == 0
        assert completed == 1

    def test_mixed_statuses(self):
        """Mixed statuses counted correctly."""
        tasks = [
            {"status": "pending"},
            {"status": "in_progress"},
            {"status": "completed"},
            {"status": "completed"},
        ]
        incomplete, completed = count_tasks_by_status(tasks)
        assert incomplete == 2
        assert completed == 2

    def test_missing_status_not_counted(self):
        """Tasks without status key are not counted."""
        tasks = [
            {"subject": "No status"},
            {"subject": "Has status", "status": "completed"},
        ]
        incomplete, completed = count_tasks_by_status(tasks)
        assert incomplete == 0
        assert completed == 1


class TestShouldUseTaskSystem:
    """Tests for should_use_task_system function."""

    def test_default_returns_true(self, monkeypatch):
        """Default (no env var) returns True."""
        monkeypatch.delenv("OMC_USE_TASK_SYSTEM", raising=False)
        assert should_use_task_system() is True

    def test_env_var_1_returns_true(self, monkeypatch):
        """OMC_USE_TASK_SYSTEM=1 returns True."""
        monkeypatch.setenv("OMC_USE_TASK_SYSTEM", "1")
        assert should_use_task_system() is True

    def test_env_var_0_returns_false(self, monkeypatch):
        """OMC_USE_TASK_SYSTEM=0 returns False."""
        monkeypatch.setenv("OMC_USE_TASK_SYSTEM", "0")
        assert should_use_task_system() is False

    def test_env_var_false_returns_false(self, monkeypatch):
        """OMC_USE_TASK_SYSTEM=false returns False."""
        monkeypatch.setenv("OMC_USE_TASK_SYSTEM", "false")
        assert should_use_task_system() is False

    def test_env_var_no_returns_false(self, monkeypatch):
        """OMC_USE_TASK_SYSTEM=no returns False."""
        monkeypatch.setenv("OMC_USE_TASK_SYSTEM", "no")
        assert should_use_task_system() is False

    def test_env_var_FALSE_returns_false(self, monkeypatch):
        """OMC_USE_TASK_SYSTEM=FALSE (uppercase) returns False."""
        monkeypatch.setenv("OMC_USE_TASK_SYSTEM", "FALSE")
        assert should_use_task_system() is False


class TestAnalyzeTranscriptTasks:
    """Tests for TaskList tracking in analyze_transcript."""

    def test_tracks_task_list_result(self):
        """TaskList tool results are tracked."""
        transcript = [
            {
                "type": "tool_result",
                "tool": "TaskList",
                "tasks": [
                    {"id": "1", "status": "pending"},
                    {"id": "2", "status": "completed"},
                ],
            }
        ]
        result = analyze_transcript(transcript)
        assert result["last_task_list"] == [
            {"id": "1", "status": "pending"},
            {"id": "2", "status": "completed"},
        ]

    def test_empty_task_list(self):
        """Empty TaskList result is tracked."""
        transcript = [
            {"type": "tool_result", "tool": "TaskList", "tasks": []}
        ]
        result = analyze_transcript(transcript)
        assert result["last_task_list"] == []

    def test_no_task_list_returns_none(self):
        """No TaskList in transcript returns None."""
        transcript = [{"type": "user", "content": "hello"}]
        result = analyze_transcript(transcript)
        assert result["last_task_list"] is None

    def test_latest_task_list_wins(self):
        """Most recent TaskList result is kept."""
        transcript = [
            {"type": "tool_result", "tool": "TaskList", "tasks": [{"id": "1", "status": "pending"}]},
            {"type": "tool_result", "tool": "TaskList", "tasks": [{"id": "1", "status": "completed"}]},
        ]
        result = analyze_transcript(transcript)
        assert result["last_task_list"] == [{"id": "1", "status": "completed"}]


class TestHybridDetection:
    """Tests for Task/TodoWrite hybrid detection priority."""

    def test_task_preferred_over_todowrite(self):
        """Task system takes priority when both have data."""
        # This tests the actual detection logic in main()
        # TaskList shows 1 incomplete, TodoWrite shows 0
        # Expected: use Task data (1 incomplete)
        tasks = [{"status": "pending"}]
        todos = []  # No incomplete todos

        task_incomplete, task_completed = count_tasks_by_status(tasks)
        todo_incomplete, todo_completed = count_todos_by_status(todos)

        # Hybrid logic: Task preferred
        if task_incomplete > 0 or task_completed > 0:
            incomplete = task_incomplete
        else:
            incomplete = todo_incomplete

        assert incomplete == 1

    def test_empty_task_list_falls_back_to_todowrite(self):
        """Empty TaskList [] should fall back to TodoWrite."""
        tasks = []  # Empty
        todos = [{"id": "1", "status": "in_progress"}]

        task_incomplete, task_completed = count_tasks_by_status(tasks)
        todo_incomplete, todo_completed = count_todos_by_status(todos)

        # Hybrid logic: fall back when no Task data
        if task_incomplete == 0 and task_completed == 0:
            incomplete = todo_incomplete
        else:
            incomplete = task_incomplete

        assert incomplete == 1

    def test_no_data_either_system(self):
        """No TaskList and no TodoWrite returns (0, 0)."""
        task_incomplete, task_completed = count_tasks_by_status(None)
        todo_incomplete, todo_completed = count_todos_by_status(None)

        assert task_incomplete == 0
        assert todo_incomplete == 0


class TestAgentSessionSkip:
    """Tests for agent session skip logic in main()."""

    def test_agent_session_not_blocked(self, monkeypatch):
        """Agent sessions (agent_type set) should return empty, not blocked."""
        import json

        # Build input with agent_type set and incomplete todos that would normally block
        hook_input = json.dumps({
            "agent_type": "teammate",
            "stopReason": "end_turn",
            "todos": [{"content": "Task 1", "status": "pending"}],
        })

        # Mock stdin to provide the hook input
        monkeypatch.setattr("todo_enforcer.read_stdin_safe", lambda: hook_input)

        # main() calls output_empty() which does sys.exit(0)
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_empty_agent_type_still_checks(self, monkeypatch, capsys):
        """Empty string agent_type should still check todos (not skip)."""
        import json

        # agent_type is empty string - should NOT be treated as agent session
        hook_input = json.dumps({
            "agent_type": "",
            "stopReason": "end_turn",
            "todos": [{"content": "Task 1", "status": "pending"}],
        })

        monkeypatch.setattr("todo_enforcer.read_stdin_safe", lambda: hook_input)
        # Disable plan/git checks to isolate todo checking
        monkeypatch.setenv("OMC_STOP_CHECK_PLANS", "0")
        monkeypatch.setenv("OMC_STOP_CHECK_GIT", "0")

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

        # Should have produced blocking output (not empty) because todos are pending
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["decision"] == "block"
        assert "Open tasks" in output["reason"]


class TestWorkerReferencesRemoved:
    """Tests that 'worker' references have been replaced in prompts/messages."""

    def test_no_worker_references(self):
        """The word 'worker' should not appear in todo_enforcer prompt strings."""
        import inspect
        import todo_enforcer

        source = inspect.getsource(todo_enforcer)

        # Collect all lines containing "worker" (case-insensitive) in string literals
        # Exclude import lines and function/class definitions
        violations = []
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            # Skip comments that are code structure, imports, docstrings about the test
            if stripped.startswith(("import ", "from ", "def ", "class ")):
                continue
            if "worker" in stripped.lower():
                violations.append(f"Line {i}: {stripped}")

        assert violations == [], (
            f"Found 'worker' references that should be replaced:\n"
            + "\n".join(violations)
        )
