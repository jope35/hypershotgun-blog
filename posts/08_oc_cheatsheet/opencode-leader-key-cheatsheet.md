# OpenCode Leader Key Cheatsheet
## `Ctrl + X` then ...

The leader key is **`Ctrl + X`** by default. After pressing it, you have ~2 seconds (`leader_timeout`, configurable in `tui.json`) to press the next key.

---

## Sessions
| Keys | Action |
|------|--------|
| `Ctrl+X` `n` | New session |
| `Ctrl+X` `l` | List / switch sessions |
| `Ctrl+X` `g` | Session timeline |
| `Ctrl+X` `s` | Status view |
| `Ctrl+X` `u` | Undo last message |
| `Ctrl+X` `r` | Redo (restore previous undo) |
| `Ctrl+X` `c` | Compact / summarize session |
| `Ctrl+X` `x` | Export conversation to Markdown |
| `Ctrl+X` `b` | Toggle sidebar |
| `Ctrl+X` `t` | Toggle timestamps |
| `Ctrl+X` `h` | Toggle help / tips |

### Session management (direct keys — no leader)
| Keys | Action |
|------|--------|
| `Ctrl+R` | Rename session |
| `Ctrl+D` | Delete session |
| `Esc` | Interrupt current session |

### Session navigation (direct keys — no leader)
| Keys | Action |
|------|--------|
| `↑` | Go to parent message (subagent navigation) |
| `↓` | Go to child message (subagent navigation) |
| `←` | Cycle parent session backward |
| `→` | Cycle parent session forward |

---

## Models & Providers
| Keys | Action |
|------|--------|
| `Ctrl+X` `m` | List & select model |
| `Ctrl+X` `a` | List & select agent |
| `F2` | Cycle recent models (forward) |
| `Shift+F2` | Cycle recent models (reverse) |
| `Ctrl+A` | List model providers |
| `Ctrl+F` | Toggle favorite model |
| `Ctrl+T` | Cycle model variants |

---

## Themes
| Keys | Action |
|------|--------|
| `Ctrl+X` `t` | List available themes |

---

## Editor / Export
| Keys | Action |
|------|--------|
| `Ctrl+X` `e` | Open external editor (`$EDITOR`) |

---

## Exit & System
| Keys | Action |
|------|--------|
| `Ctrl+C` | Exit OpenCode |
| `Ctrl+D` | Exit OpenCode (if no content in input) |
| `Ctrl+X` `q` | Exit OpenCode |
| `Ctrl+Z` | Suspend terminal (POSIX; `none` on Windows) |

---

## Command Palette
| Keys | Action |
|------|--------|
| `Ctrl+P` | Open command palette |

---

## File References
| Syntax | Action |
|--------|--------|
| `@file` | Reference a file in your prompt (fuzzy search) |
| `@alias` | Reference configured file alias |
| `@alias/` | Autocomplete files inside alias |

---

## Which-Key Overlay (direct keys — no leader)
| Keys | Action |
|------|--------|
| `Ctrl+Alt+K` | Toggle which-key overlay |
| `Ctrl+Alt+Shift+K` | Toggle which-key layout |
| `Ctrl+Alt+Shift+P` | Toggle which-key pending |
| `Ctrl+Alt+←` `Ctrl+Alt+[` | Previous keybind group |
| `Ctrl+Alt+→` `Ctrl+Alt+]` | Next keybind group |
| `Ctrl+Alt+↑` `Ctrl+Alt+P` | Scroll up |
| `Ctrl+Alt+↓` `Ctrl+Alt+N` | Scroll down |
| `Ctrl+Alt+PageUp` | Page up |
| `Ctrl+Alt+PageDown` | Page down |
| `Ctrl+Alt+Home` | Go to home |
| `Ctrl+Alt+End` | Go to end |

---

## Prompt Input — Editing (Emacs / Readline style)
| Keys | Action |
|------|--------|
| `Ctrl+A` | Move to start of line |
| `Ctrl+E` | Move to end of line |
| `Ctrl+B` | Move cursor back one character |
| `Ctrl+F` | Move cursor forward one character |
| `Alt+B` | Move cursor back one word |
| `Alt+F` | Move cursor forward one word |
| `Ctrl+D` | Delete character under cursor |
| `Ctrl+K` | Kill to end of line |
| `Ctrl+U` | Kill to start of line |
| `Ctrl+W` | Kill previous word |
| `Alt+D` | Kill next word |
| `Ctrl+T` | Transpose characters |
| `Ctrl+G` | Cancel popovers / abort running response |

### Prompt Input — Movement
| Keys | Action |
|------|--------|
| `Left` `Ctrl+B` | Move left |
| `Right` `Ctrl+F` | Move right |
| `Home` | Buffer home |
| `End` | Buffer end |
| `Ctrl+Left` `Alt+Left` | Move word backward |
| `Ctrl+Right` `Alt+Right` | Move word forward |

### Prompt Input — Selection
| Keys | Action |
|------|--------|
| `Shift+←` | Select left |
| `Shift+→` | Select right |
| `Shift+↑` `Shift+↓` | Select up/down |
| `Ctrl+Shift+A` | Select to line start |
| `Ctrl+Shift+E` | Select to line end |
| `Alt+Shift+A` | Visual line home |
| `Alt+Shift+E` | Visual line end |
| `Shift+Home` | Select buffer home |
| `Shift+End` | Select buffer end |

### Prompt Input — Deletion
| Keys | Action |
|------|--------|
| `Ctrl+Shift+D` | Delete entire line |
| `Ctrl+K` | Delete to end of line |
| `Ctrl+U` | Delete to start of line |
| `Ctrl+D` `Delete` `Shift+Delete` | Delete character |
| `Alt+D` `Alt+Delete` `Ctrl+Delete` | Delete word forward |
| `Ctrl+W` `Ctrl+Backspace` `Alt+Backspace` | Delete word backward |
| `Backspace` `Shift+Backspace` | Backspace |

### Prompt Input — Undo / Redo
| Keys | Action |
|------|--------|
| `Ctrl+Minus` `Ctrl+Z` | Undo text |
| `Ctrl+.` `Ctrl+Shift+Z` | Redo text |

### Prompt Input — Submit / Newline
| Keys | Action |
|------|--------|
| `Return` | Submit prompt |
| `Shift+Enter` `Ctrl+Enter` `Alt+Enter` `Ctrl+J` | New line |

---

## Message Viewing & Navigation (direct keys — no leader)
| Keys | Action |
|------|--------|
| `PageUp` `Ctrl+Alt+B` | Page up |
| `PageDown` `Ctrl+Alt+F` | Page down |
| `Ctrl+Alt+Y` | Line up |
| `Ctrl+Alt+E` | Line down |
| `Ctrl+Alt+U` | Half page up |
| `Ctrl+Alt+D` | Half page down |
| `Ctrl+G` `Home` | First message |
| `Ctrl+Alt+G` `End` | Last message |
| `Ctrl+Alt+K` | Toggle thinking blocks |
| `Ctrl+X` `y` | Copy last message |

---

## Autocomplete & History (direct keys — no leader)
| Keys | Action |
|------|--------|
| `Up` | Previous history entry |
| `Down` | Next history entry |
| `Up` `Ctrl+P` | Previous autocomplete option |
| `Down` `Ctrl+N` | Next autocomplete option |
| `Esc` | Hide autocomplete |

---

## Dialogs (direct keys — no leader)
| Keys | Action |
|------|--------|
| `Up` `Ctrl+P` | Previous option |
| `Down` `Ctrl+N` | Next option |
| `PageUp` | Page up |
| `PageDown` | Page down |
| `Home` | Home |
| `End` | End |
| `Return` | Submit |
| `Space` | Toggle (MCP, plugins) |
| `Shift+I` | Install plugin |

---

## Plugins & MCP (direct keys — no leader)
| Keys | Action |
|------|--------|
| `Space` | Toggle plugins |
| `Space` | Toggle MCP in dialogs |

---

## Stash Management
| Keys | Action |
|------|--------|
| `Ctrl+D` | Delete stash entry |

---

## Notes
- **Leader key & timeout**: Default is `Ctrl+X` with a 2-second timeout. Configure in `tui.json` via `leader_timeout`.
- **Non-leader bindings**: Many navigation, editing, and system keys work directly without the leader prefix. See the tables above.
- **Customization**: All keybinds live in `tui.json` (or `tui.jsonc`). Built-in defaults are merged — only override what you need.
- **Windows**: `input_undo` defaults to `Ctrl+Z,Ctrl+Minus,Super+Z`; `terminal_suspend` is forced to `none` because native Windows terminals don't support POSIX suspend.
- **Shell commands in TUI**: Prefix a message with `!` to run a shell command (e.g., `! ls -la`).
- **` ` (space) notation**: In `tui.json`, a leading space before a key means it's relative to the leader key (e.g., `" e"` = `Ctrl+X` `E`).

### Source
- [OpenCode Keybinds Docs](https://opencode.ai/docs/keybinds/)
- [OpenCode TUI Docs](https://opencode.ai/docs/tui/)
