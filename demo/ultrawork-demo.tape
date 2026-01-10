# oh-my-claude Demo - Ultrawork Mode
# Shows parallel agent execution building from scratch
#
# Requirements: VHS, Claude Code CLI, oh-my-claude plugin installed
# Generate: vhs demo/ultrawork-demo.tape

Output demo/ultrawork-demo.gif

# Terminal appearance
Set Shell "bash"
Set FontSize 14
Set FontFamily "JetBrains Mono"
Set Width 1200
Set Height 800
Set Padding 20
Set WindowBar Colorful
Set Theme "Catppuccin Mocha"
Set TypingSpeed 30ms
Set PlaybackSpeed 10.0

# Minimal setup - just empty directory
Type "cd /tmp && rm -rf myapp && mkdir myapp && cd myapp"
Enter
Sleep 500ms

# Start Claude with permissions skipped and reduced banner (IS_DEMO=1)
Type "IS_DEMO=1 claude --dangerously-skip-permissions"
Enter
Sleep 3s

# Accept trust prompt
Enter
Sleep 3s

# Ambitious prompt that forces the full agent team:
# - Scout: will explore (find nothing)
# - Architect: must plan the entire implementation
# - Workers: implement auth, API, tests, docs in parallel
Type "build a Node.js REST API for a todo app with JWT authentication, input validation, unit tests, and API documentation - ulw"
Enter

# Record for 10 minutes to capture full agent orchestration
Sleep 600s

Ctrl+C
Sleep 500ms
Type "/exit"
Enter
Sleep 1s
