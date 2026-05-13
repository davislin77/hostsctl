# hostsctl

[繁體中文說明](README.zh-TW.md)

Interactive TUI for managing `/etc/hosts` mappings. Switch IPs per hostname without manually editing the file.

![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| macOS / Linux | — | Windows not supported (`tty`/`termios` dependency) |
| Python | 3.7+ | `python3 --version` |
| PyYAML | any | `pip3 install pyyaml` |
| sudo | — | Required for writing to `/etc/hosts` |

---

## Installation

```bash
git clone https://github.com/davislin77/hostsctl.git
pip3 install pyyaml
```

Add an alias to youor shell rc:

```zsh
# example: `~/.zshrc`
alias hostsctl="python3 /path/to/hostsctl/bin/hostsctl.py"
```

Reload the shell:

```bash
source ~/.zshrc
```

---

## Usage

```bash
hostsctl
```

---

## How it works

hostsctl manages a dedicated section inside `/etc/hosts`, leaving all other entries untouched:

```
# existing system entries
127.0.0.1  localhost
...

# --- BEGIN hostsctl ---
192.168.70.169 test.example.com  # staging
10.0.0.1       test.example.com  # (hidden, commented out)
# --- END hostsctl ---
```

User data (IP list, host list, mappings) is stored in `~/.config/hostsctl/data.yaml`.  
Language preference is stored in `~/.config/hostsctl/config.yaml`.  
Writing to `/etc/hosts` requires `sudo` — you will be prompted on first write.

---

## Navigation

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move cursor |
| `→` / `Enter` | Select |
| `←` | Back |
| `Ctrl+C` | Cancel input / Quit |

---

## License

MIT
