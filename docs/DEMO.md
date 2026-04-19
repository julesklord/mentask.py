# askgem Demo & Terminal Recordings

This guide explains how to create, maintain, and share terminal demonstrations of **askgem** using **VHS** (Terminal GIF recorder).

---

## What is VHS?

[VHS](https://github.com/charmbracelet/vhs) is a lightweight tool that converts terminal `.tape` scripts into animated GIFs or MP4 videos. It's perfect for:

- 📹 Creating reproducible demos
- 🎯 Documenting workflows step-by-step
- 🚀 Sharing on GitHub without external hosting
- 📊 Showing real terminal output

---

## Installation

### macOS
```bash
brew install charmbracelet/tap/vhs
```

### Linux
```bash
# Download the latest release
wget https://github.com/charmbracelet/vhs/releases/download/v0.5.0/vhs-linux-amd64
chmod +x vhs-linux-amd64
sudo mv vhs-linux-amd64 /usr/local/bin/vhs
```

### Windows
```powershell
# Via Scoop
scoop install vhs

# Or download from: https://github.com/charmbracelet/vhs/releases
```

---

## The Demo Script

Located at: **`docs/demo.tape`**

### Structure

```tape
# askgem Demo - Terminal Recording
# Record with: vhs < docs/demo.tape > docs/demo.gif
# Requires: vhs (https://github.com/charmbracelet/vhs)

Output docs/demo.gif              # Output file path

Set Shell bash                    # Shell to use
Set FontSize 14                   # Terminal font size
Set Width 1200                    # Terminal width (pixels)
Set Height 600                    # Terminal height (pixels)
Set TypingSpeed 50ms              # Speed of typing simulation
Set PlaybackSpeed 1.0             # Playback speed (1.0 = real-time)

# Commands...
Type "command"                    # Type a command
Enter                             # Press Enter
Sleep 2s                          # Wait 2 seconds
```

---

## Generating the Demo

### Standard GIF Output

```bash
cd askgem.py
vhs < docs/demo.tape > docs/demo.gif
```

This creates `docs/demo.gif` (animated GIF, ~500KB).

### MP4 Output (Higher Quality)

```bash
vhs < docs/demo.tape > docs/demo.mp4
```

MP4 is smaller and higher quality, but GitHub GIF previews are more accessible.

### With Custom Output Path

Edit `docs/demo.tape` and change the first line:

```tape
Output /path/to/custom/demo.gif
```

Then run:
```bash
vhs < docs/demo.tape
```

---

## Creating Your Own Demo

### Step 1: Create a `.tape` File

```bash
cat > docs/my-demo.tape << 'EOF'
Output docs/my-demo.gif
Set Shell bash
Set FontSize 14
Set Width 1200
Set Height 600
Set TypingSpeed 50ms

Type "# My Custom askgem Demo"
Enter
Sleep 1s

Type "askgem"
Enter
Sleep 2s

Type "List all Python files in src/"
Enter
Sleep 3s

Type "/exit"
Enter
EOF
```

### Step 2: Generate the Recording

```bash
vhs < docs/my-demo.tape
```

### Step 3: Commit and Reference

```bash
git add docs/my-demo.gif docs/my-demo.tape
git commit -m "docs: add custom askgem demo recording"
```

### Step 4: Embed in Markdown

```markdown
## Demo: [Your Title]

![askgem demo](docs/my-demo.gif)

**Description of what's happening in this demo...**
```

---

## VHS Tape Language Reference

### Output

```tape
Output /path/to/file.gif          # Required; GIF format
Output /path/to/file.mp4          # MP4 format (higher quality)
```

### Settings

| Command | Values | Default | Notes |
|---------|--------|---------|-------|
| `Set FontSize` | 8-32 | 14 | Terminal font size |
| `Set Width` | pixels | 1200 | Terminal width |
| `Set Height` | pixels 600 | Terminal height |
| `Set TypingSpeed` | ms | 50ms | Delay between key presses |
| `Set PlaybackSpeed` | float | 1.0 | 0.5 = half-speed, 2.0 = double-speed |
| `Set Shell` | bash, zsh, fish, powershell | bash | Shell interpreter |
| `Set Padding` | pixels | 10 | Border padding |
| `Set LineHeight` | float | 1.2 | Line spacing |
| `Set Theme` | terminal theme name | Default | See [Charm themes](https://github.com/charmbracelet/vhs/blob/main/themes.go) |

### Commands

| Command | Example | Notes |
|---------|---------|-------|
| `Type` | `Type "hello"` | Simulate typing text |
| `Enter` | `Enter` | Press Enter key |
| `Backspace` | `Backspace 5` | Press backspace N times |
| `Down` | `Down 3` | Press Down arrow 3 times |
| `Sleep` | `Sleep 2s` | Wait 2 seconds (supports ms, s) |
| `Show` | `Show` | Make cursor visible |
| `Hide` | `Hide` | Hide cursor |
| `Ctrl+C` | `Ctrl+C` | Send Ctrl+C |
| `Escape` | `Escape` | Send Escape key |

---

## Best Practices

### 1. Keep It Short
- **Ideal length**: 30-60 seconds
- **Max length**: 2 minutes
- Viewers should grasp the core feature quickly

### 2. Slow Down Typing
```tape
Set TypingSpeed 80ms   # Easier to follow
Set PlaybackSpeed 0.8  # Additional slowdown
```

### 3. Add Pauses
```tape
Sleep 1s               # Let output settle
Sleep 2s               # Let user read
```

### 4. Use Clear Commands
```tape
Type "# Clear Section"
Enter
Type "echo 'Starting demo...'"
Enter
```

### 5. Handle Errors Gracefully
```tape
Type "command-that-might-fail || echo 'Error handled'"
Enter
```

### 6. Document in Header
```tape
# Demo: Show offline mode with cached results
# Key features: caching, offline resilience
# Duration: ~45 seconds
```

---

## Troubleshooting

### "vhs: command not found"
Install VHS (see [Installation](#installation) above).

### GIF is too large (>10MB)
- Reduce `Set Width` and `Set Height`
- Increase `Set PlaybackSpeed` to speed up recording
- Use MP4 format instead: `Output docs/demo.mp4`

### GIF is pixelated or blurry
- Increase `Set FontSize`
- Use MP4 format (preserves clarity better)
- Reduce `Set Width` and `Set Height`

### Recording shows wrong shell
Ensure `Set Shell` matches your system:
```bash
echo $SHELL  # Check your current shell
```

### Text appears too fast
```tape
Set TypingSpeed 100ms   # Increase from default 50ms
Set PlaybackSpeed 0.7   # Slow down playback
```

---

## Demo Checklist

Before committing a new demo:

- [ ] `.tape` file is readable and well-commented
- [ ] GIF/MP4 generated successfully
- [ ] Recording is 30-60 seconds (or justified if longer)
- [ ] Typing is at a readable speed
- [ ] All pauses make sense (not too fast, not boring)
- [ ] Error handling is shown (if applicable)
- [ ] Embedded in docs with descriptive caption
- [ ] Both `.tape` source and `.gif`/`.mp4` are committed

---

## Example Demos

### Basic Usage
**File**: `docs/demo.tape`  
**Focus**: Installation → startup → basic command → history  
**Duration**: ~45 seconds

### Advanced Workflow
**File**: `docs/advanced-demo.tape` (to create)  
**Focus**: Multi-file editing → mission tracking → security prompts  
**Duration**: ~2 minutes

### Multimodal Features
**File**: `docs/multimodal-demo.tape` (to create)  
**Focus**: Image analysis → code generation → validation  
**Duration**: ~90 seconds

---

## Embedding in GitHub

### GIF Preview
```markdown
![askgem Demo](docs/demo.gif)
```

### Link to GIF
```markdown
[View demo recording →](docs/demo.gif)
```

### Link to Full Video
```markdown
For a full walkthrough, see our [extended demo](docs/advanced-demo.mp4).
```

---

## Automation (Optional)

Generate all demos automatically on CI/CD:

```bash
# .github/workflows/demo.yml
name: Generate Terminal Demos
on: [push]
jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          brew install charmbracelet/tap/vhs
          vhs < docs/demo.tape
          vhs < docs/advanced-demo.tape
      - uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "chore: regenerate terminal demos"
```

---

## Resources

- **VHS GitHub**: https://github.com/charmbracelet/vhs
- **VHS Docs**: https://github.com/charmbracelet/vhs/tree/main/docs
- **Charm.sh Community**: https://charm.sh/
- **Terminal Recording Inspiration**: https://github.com/charmbracelet/bubble-tea/blob/main/examples/

---

**Last Updated**: April 19, 2026  
**VHS Version**: 0.5.0+  
**askgem Version**: 0.14.0+
