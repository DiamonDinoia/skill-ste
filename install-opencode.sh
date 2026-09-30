#!/usr/bin/env bash
# Symlink the ste skill and its /ste command shim into opencode. Writes only
# opencode's own directories: the plugin-marketplace harnesses get the skill
# without this script (no duplicate installs).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p ~/.config/opencode/skills ~/.config/opencode/commands

ln -sfn "$ROOT/skills/ste" ~/.config/opencode/skills/ste
ln -sfn "$ROOT/.opencode/command/ste.md" ~/.config/opencode/commands/ste.md

echo "linked; restart opencode to pick the skill up"
