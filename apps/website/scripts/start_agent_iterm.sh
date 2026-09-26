#!/usr/bin/env bash
# HSB Sales OS — Launch Agent in a New iTerm2 Window
set -e

REPO_DIR="/Users/joelcherinodiaz/Projekte/hsb-boden"

osascript <<EOF
tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "cd $REPO_DIR && gemini --approval-mode auto_edit"
    end tell
end tell
EOF

echo "✅ Neues iTerm2-Fenster erfolgreich gestartet mit Gemini CLI in $REPO_DIR"
