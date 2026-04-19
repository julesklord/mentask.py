# askgem Demo - Terminal Recording
# Record with: vhs < docs/demo.tape > docs/demo.gif
# Requires: vhs (https://github.com/charmbracelet/vhs)

Output docs/demo.gif

Set Shell bash
Set FontSize 14
Set Width 1200
Set Height 600
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

# Welcome screen
Type "# askgem — Autonomous AI Coding Agent Demo"
Enter
Sleep 1s

Type "## Starting askgem session..."
Enter
Sleep 500ms

# Show help
Type "askgem --help"
Enter
Sleep 2s

# Clear and show config
Type "clear"
Enter
Sleep 500ms

Type "# Setting up environment..."
Enter
Sleep 500ms

Type "export GOOGLE_API_KEY='your-key-here'  # Required for Gemini API"
Enter
Sleep 500ms

# Start askgem
Type "askgem"
Enter
Sleep 2s

# Demonstrate interactive prompt
Type "/help"
Enter
Sleep 1s

Type "Create a Python function that validates email addresses with regex"
Enter
Sleep 3s

# Show mission tracking
Type "/mission status"
Enter
Sleep 1s

# Show history
Type "/history list"
Enter
Sleep 1.5s

# Exit demo
Type "/exit"
Enter
Sleep 500ms

Type "echo '✅ askgem session complete'"
Enter
Sleep 1s
