# robium — terminal demo tape (charmbracelet/vhs)
#
# Renders the REAL `robium-ai` CLI install experience into a shareable GIF.
# Render:  vhs assets/demo-terminal.tape   ->   assets/demo-terminal.gif
# Install vhs if needed:  brew install vhs   (or see https://github.com/charmbracelet/vhs)
#
# HONESTY CONTRACT (do not violate when editing this tape):
#   - Every line that ends in `Enter` runs a REAL command and shows its REAL output.
#     `npx -y robium-ai ...` is the published package (npmjs.com/package/robium-ai);
#     output is whatever the CLI actually prints on the recording machine.
#   - Lines that are only *shown* (the manual `/plugin` commands you type inside
#     Claude Code, and the natural-language prompt) are typed and then CLEARED with
#     Ctrl+C — they are never executed, so the GIF never shows fabricated output.
#   - No scripted agent/model responses, build logs, or sim frames live here.
#     The sim payoff is the human-recorded footage (see docs/demo-storyboard.md).
#
# Record on a machine with Node >=18 on PATH, network access, and (ideally)
# Claude Code installed so `install`/`doctor` print their real success lines.

Output assets/demo-terminal.gif

Require npx

Set Shell "bash"
Set FontSize 22
Set Width 1200
Set Height 720
Set Padding 24
Set Margin 12
Set MarginFill "#1e1e2e"
Set BorderRadius 10
Set Theme "Catppuccin Mocha"
Set TypingSpeed 55ms
Set PlaybackSpeed 1.0

# --- 1. The one-command install (real output) --------------------------------
Type "npx -y robium-ai install"
Sleep 500ms
Enter
Sleep 9s

# --- 2. Show the manual alternative you'd type INSIDE Claude Code -------------
#        (typed for display, then cleared with Ctrl+C — never executed)
Type "# ...or add it by hand inside Claude Code:"
Sleep 1s
Ctrl+C
Type "/plugin marketplace add robium-ai/robium"
Sleep 1500ms
Ctrl+C
Type "/plugin install robium@robium"
Sleep 1500ms
Ctrl+C
Sleep 500ms

# --- 3. Check the machine is ready for robotics work (real output) ------------
Type "npx -y robium-ai doctor"
Sleep 500ms
Enter
Sleep 6s

# --- 4. Browse the real skill catalog (real output) --------------------------
Type "npx -y robium-ai skills nav"
Sleep 500ms
Enter
Sleep 4s

# --- 5. The handoff: what you type next, in plain language -------------------
#        (typed for display, then cleared — the sim payoff is the recorded video)
Type "# then just ask, in plain language:"
Sleep 1s
Ctrl+C
Type "  build me a mobile robot that navigates a warehouse in simulation"
Sleep 3s
Ctrl+C

Sleep 2s
