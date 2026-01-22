# oh-my-claude Demo - Ultrawork Mode
# Shows parallel agent orchestration with focused task
#
# Prerequisites:
#   1. Run: ./demo/setup-demo.sh
#   2. Then: vhs demo/ultrawork-demo.tape

Output demo/ultrawork-demo.gif

# Terminal appearance
Set Shell "bash"
Set FontSize 14
Set FontFamily "JetBrains Mono"
Set Width 1400
Set Height 900
Set Padding 20
Set WindowBar Colorful
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms
Set PlaybackSpeed 10.0

# Start in empty demo directory (from scratch)
Type "cd /tmp/myapp"
Enter
Sleep 500ms

# Start Claude with permissions skipped and reduced banner
Type "IS_DEMO=1 claude --dangerously-skip-permissions"
Enter
Sleep 3s

# Accept trust prompt
Enter
Sleep 3s

# Big ask that forces full agent orchestration:
# - Architect: must plan the entire system
# - Workers (parallel): auth, tasks API, validation, tests
# - Validator: runs the test suite
Type "Build a task management REST API from scratch. I need: 1) User auth with JWT (register, login, protected routes), 2) Task CRUD endpoints (create, list, get, update, delete) with user ownership, 3) Input validation using zod for all endpoints, 4) Proper error handling middleware that returns consistent JSON errors, 5) Unit tests for auth logic and integration tests for all endpoints. Use Express with ES modules, structure the code cleanly with separate routes/controllers/middleware folders. Make it production-ready. - ultrawork"
Enter

# Record for 5 minutes - focused task completes faster
Sleep 300s

Ctrl+C
Sleep 500ms
Type "/exit"
Enter
Sleep 1s
