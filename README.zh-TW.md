# hostsctl

以互動式 TUI 管理 `/etc/hosts` 對應設定，快速切換各 hostname 對應的 IP，無需手動編輯檔案。

![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)

---

## 系統需求

| 項目 | 版本 | 說明 |
|------|------|------|
| macOS / Linux | — | 不支援 Windows（相依 `tty`/`termios`） |
| Python | 3.7+ | `python3 --version` |
| PyYAML | 任意版本 | `pip3 install pyyaml` |
| sudo | — | 寫入 `/etc/hosts` 需要權限 |

---

## 安裝

```bash
git clone https://github.com/davislin77/hostsctl.git
pip3 install pyyaml
```

在 `~/.zshrc` 加入 alias：

```zsh
alias hostsctl="python3 /path/to/hostsctl/bin/hostsctl.py"
```

重新載入 shell：

```bash
source ~/.zshrc
```

---

## 使用方式

```bash
hostsctl
```

---

## 運作原理

hostsctl 在 `/etc/hosts` 中管理一個專屬區段，其餘內容完全不異動：

```
# 系統原有設定，不受影響
127.0.0.1  localhost
...

# --- BEGIN hostsctl ---
192.168.70.169 test.example.com  # staging
# 10.0.0.1     test.example.com  # （隱藏，已註解）
# --- END hostsctl ---
```

| 檔案 | 位置 |
|------|------|
| IP / Host / Mapping 資料 | `~/.config/hostsctl/data.yaml` |
| 語言偏好 | `~/.config/hostsctl/config.yaml` |
| 翻譯字典 | 隨套件安裝，read-only |

寫入 `/etc/hosts` 時會透過 `sudo tee`，首次執行會要求輸入密碼。

---

## 鍵盤操作

| 按鍵 | 動作 |
|------|------|
| `↑` / `↓` | 移動游標 |
| `→` / `Enter` | 確認選擇 |
| `←` | 返回上層 |
| `Ctrl+C` | 取消輸入 / 離開程式 |

---

## License

MIT
