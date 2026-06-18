#!/usr/bin/env python3
import os, sys, select, tty, termios, subprocess
import yaml

# ── paths ─────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.expanduser('~/.config/hostsctl')
DATA_FILE   = os.path.join(CONFIG_DIR, 'data.yaml')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.yaml')
LANG_FILE   = os.path.join(_SCRIPT_DIR, '..', 'assets', 'lang.yaml')
HOSTS_FILE  = '/etc/hosts'

MARKER_BEGIN = '# --- BEGIN hostsctl ---'
MARKER_END   = '# --- END hostsctl ---'

# ── ANSI ──────────────────────────────────────────────────────────────────────
BOLD = '\033[1m'; DIM = '\033[2m'; INV = '\033[7m'; CYAN = '\033[36m'; RST = '\033[0m'
CLS  = '\033[2J\033[H'

UP, DOWN, RIGHT, LEFT, ENTER, ESC = 'UP', 'DOWN', 'RIGHT', 'LEFT', 'ENTER', 'ESC'
SEP   = object()   # non-selectable separator sentinel
_BACK = object()   # default back-label sentinel

# ── keyboard ──────────────────────────────────────────────────────────────────

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        b = os.read(fd, 1)
        if b == b'\x03':                       # Ctrl+C -> quit
            sys.stdout.write(RST + '\n')
            sys.exit(0)
        if b == b'\x1b':
            r, _, _ = select.select([fd], [], [], 0.15)
            if r:
                b2 = os.read(fd, 1)
                if b2 == b'[':
                    r2, _, _ = select.select([fd], [], [], 0.15)
                    if r2:
                        b3 = os.read(fd, 1)
                        return {'A': UP, 'B': DOWN, 'C': RIGHT, 'D': LEFT}.get(
                            b3.decode('ascii', errors=''), ESC)
            return ESC
        c = b.decode('utf-8', errors='ignore')
        return ENTER if c in ('\r', '\n') else c
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ── i18n ──────────────────────────────────────────────────────────────────────

_lang = 'en'
_T: dict = {}

def _load_lang():
    global _lang, _T
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = yaml.safe_load(f) or {}
        _lang = cfg.get('lang', 'en')
    if os.path.exists(LANG_FILE):
        with open(LANG_FILE) as f:
            all_langs = yaml.safe_load(f) or {}
        _T = all_langs.get(_lang, all_langs.get('en', {}))

def _save_lang():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = yaml.safe_load(f) or {}
    cfg['lang'] = _lang
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

def t(key, **kw):
    val = _T.get(key, key)
    return val.format(**kw) if kw else val

# ── TUI ───────────────────────────────────────────────────────────────────────

def menu(title, items, subtitle=None, back=_BACK):
    all_opts = list(items)
    if back is _BACK:
        back = t('back')
    if back:
        all_opts.append(back)

    # logical index list: excludes SEP items
    log   = [i for i, o in enumerate(all_opts) if o is not SEP]
    n_log = len(log)
    bi    = n_log - 1 if back else None   # logical index of the back item

    cur = 0

    while True:
        act = log[cur]   # actual index in all_opts

        sys.stdout.write(CLS)
        print(f'\n{BOLD}[ {title} ]{RST}')
        print('─' * 44)
        if subtitle:
            for s in ([subtitle] if isinstance(subtitle, str) else subtitle):
                print(f'  {DIM}{s}{RST}')
            print()
        for i, o in enumerate(all_opts):
            if o is SEP:
                print(f'   {DIM}{"─" * 40}{RST}')
            elif i == act:
                print(f'  {BOLD}› {o}{RST}')
            else:
                is_back_item = back and i == log[-1]
                print(f'    {DIM if is_back_item else ""}{o}{RST}')
        print(f'\n  {DIM}{t("key_hint")}{RST}')
        sys.stdout.flush()

        k = getch()
        if k == UP:
            cur = (cur - 1) % n_log
        elif k == DOWN:
            cur = (cur + 1) % n_log
        elif k in (ENTER, RIGHT):
            if bi is not None and cur == bi:
                return None
            return (cur, all_opts[act])
        elif k in (LEFT, ESC, 'q'):
            return None

def notify(msg):
    sys.stdout.write(CLS)
    print(f'\n  {msg}')
    print(f'\n  {DIM}{t("press_any_key")}{RST}', end='', flush=True)
    getch()

def ask(label, allow_empty=False, hint=None):
    sys.stdout.write(CLS)
    if hint:
        print(f'\n  {DIM}{hint}{RST}')
    print(f'  {DIM}{t("hint_ctrl_c")}{RST}')
    while True:
        try:
            val = input(f'\n  {label}: ').strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if val or allow_empty:
            return val
        print(f'  {t("err_required")}')

def confirm(title, subtitle=None):
    r = menu(title, [t('confirm_btn'), t('cancel')], subtitle=subtitle, back=None)
    return r is not None and r[0] == 0

# ── data ──────────────────────────────────────────────────────────────────────
#
# hosts.yaml schema:
#   entries:
#     - alias: local
#       ip: 1        # key into ips
#       host: 1      # key into hosts
#   ips:
#     1: {ip: 127.0.0.1, name: local}
#   hosts:
#     1: foo.bar.com
#
# Each entry produces one line in the hosts file:
#   127.0.0.1 foo.bar.com  # local

def load():
    if not os.path.exists(DATA_FILE):
        return {'entries': [], 'ips': {}, 'hosts': {}}
    with open(DATA_FILE) as f:
        d = yaml.safe_load(f) or {}
    raw = d.get('entries') or []
    return {
        'entries': [e for e in raw if 'host' in e and 'ip' in e],
        'ips':     d.get('ips') or {},
        'hosts':   d.get('hosts') or {},
    }

def save(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    _write_hosts(data)

def _write_hosts(data):
    section_lines = []
    for e in data.get('entries') or []:
        ip_rec   = data['ips'].get(e['ip'])
        hostname = data['hosts'].get(e['host'])
        if ip_rec and hostname:
            cmt  = f'  # {e["alias"]}' if e.get('alias') else ''
            line = f'{ip_rec["ip"]} {hostname}{cmt}\n'
            section_lines.append(f'# {line}' if e.get('hidden') else line)

    section = [MARKER_BEGIN + '\n'] + section_lines + [MARKER_END + '\n']

    try:
        with open(HOSTS_FILE, 'r') as f:
            content = f.readlines()
    except FileNotFoundError:
        content = []

    begins = [i for i, l in enumerate(content) if l.strip() == MARKER_BEGIN]
    ends   = [i for i, l in enumerate(content) if l.strip() == MARKER_END]

    if begins and ends:
        new_content = content[:begins[0]] + section + content[ends[0] + 1:]
    else:
        if content and content[-1] != '\n':
            content.append('\n')
        new_content = content + ['\n'] + section

    result = subprocess.run(
        ['sudo', 'tee', HOSTS_FILE],
        input=''.join(new_content).encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode().strip())

def _next_id(d):
    keys = [k for k in d if isinstance(k, int)]
    return max(keys, default=0) + 1

# ── helpers ───────────────────────────────────────────────────────────────────

def display_width(s):
    import unicodedata
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w

def ljust_display(s, width):
    pad = max(0, width - display_width(s))
    return s + ' ' * pad

def ip_label(ip_rec, ip_width=0):
    if not ip_rec:
        return '?'
    ip = ip_rec['ip']
    ip_str = ljust_display(ip, ip_width) if ip_width else ip
    return f'{ip_str}  ({ip_rec["name"]})' if ip_rec.get('name') else ip

def entry_label(data, e, alias_width=0, host_width=0, ip_width=0):
    hostname = data['hosts'].get(e['host'], '?')
    ip_rec   = data['ips'].get(e['ip'])
    hidden   = t('hidden_tag') if e.get('hidden') else ''
    if alias_width:
        prefix = f'[{ljust_display(e.get("alias") or "", alias_width)}] '
    else:
        prefix = f'[{e["alias"]}] ' if e.get('alias') else ''
    host_str = ljust_display(hostname, host_width) if host_width else hostname
    if ip_rec:
        addr = ip_rec['ip']
        if ip_rec.get('name'):
            ip_str = f'{ljust_display(addr, ip_width) if ip_width else addr}  ({ip_rec["name"]})'
        else:
            ip_str = addr
    else:
        ip_str = '?'
    return f'{prefix}{host_str}  →  {ip_str}{hidden}'

# ── mapping ───────────────────────────────────────────────────────────────────

def _entry_detail(data, idx):
    e = data['entries'][idx]
    while True:
        toggle = t('show_mapping') if e.get('hidden') else t('hide_mapping')
        r = menu(entry_label(data, e),
                 [t('switch_ip'), t('edit_alias'), toggle, t('remove_mapping')])
        if r is None:
            return
        if r[0] == 0:
            _entry_switch_ip(data, e)
        elif r[0] == 1:
            cur_alias = e.get('alias') or t('none_value')
            new_alias = ask(t('prompt_alias_edit', current=cur_alias), allow_empty=True)
            if new_alias is None:
                continue
            e['alias'] = new_alias
            save(data)
            notify(t('ok_updated'))
        elif r[0] == 2:
            e['hidden'] = not e.get('hidden', False)
            save(data)
            notify(t('ok_hidden') if e['hidden'] else t('ok_shown'))
        else:
            hostname = data['hosts'].get(e['host'], '?')
            if confirm(t('confirm_remove_mapping', host=hostname)):
                data['entries'].pop(idx)
                save(data)
                notify(t('ok_removed'))
                return

def _entry_switch_ip(data, e):
    ips = data['ips']
    if not ips:
        notify(t('err_no_ips_add_first'))
        return
    ids      = list(ips.keys())
    ip_w     = max((display_width(ips[i]['ip']) for i in ids), default=0)
    hostname = data['hosts'].get(e['host'], '?')
    cur_ip   = f'{RST}{CYAN}{ip_label(ips.get(e["ip"]))}{RST}'
    r = menu(t('switch_ip_for', host=hostname),
             [ip_label(ips[i], ip_w) for i in ids],
             subtitle=t('current_ip', ip=cur_ip))
    if r is None:
        return
    e['ip'] = ids[r[0]]
    save(data)
    notify(t('ok_switched', target=ip_label(ips[ids[r[0]]])))

def _entry_add(data):
    if not data['hosts']:
        notify(t('err_no_hosts_add_first'))
        return
    if not data['ips']:
        notify(t('err_no_ips_add_first'))
        return

    host_ids = list(data['hosts'].keys())
    r = menu(t('select_host'), [data['hosts'][i] for i in host_ids], back=t('cancel'))
    if r is None:
        return
    host_id = host_ids[r[0]]

    ip_ids = list(data['ips'].keys())
    ip_w   = max((display_width(data['ips'][i]['ip']) for i in ip_ids), default=0)
    r = menu(t('select_ip'), [ip_label(data['ips'][i], ip_w) for i in ip_ids], back=t('cancel'))
    if r is None:
        return
    ip_id = ip_ids[r[0]]

    alias = ask(t('prompt_alias_optional'), allow_empty=True)
    if alias is None:
        return
    data['entries'].append({'alias': alias, 'ip': ip_id, 'host': host_id})
    save(data)
    notify(t('ok_mapping_added'))

# ── IP management ─────────────────────────────────────────────────────────────

def do_ip(data):
    while True:
        ips   = data['ips']
        ids   = list(ips.keys())
        ip_w  = max((display_width(ips[i]['ip']) for i in ids), default=0) if ids else 0
        items = [ip_label(ips[i], ip_w) for i in ids]
        if ids:
            items.append(SEP)
        items.append(t('add_ip'))
        r = menu(t('manage_ip'), items)
        if r is None:
            return
        idx = r[0]
        if idx < len(ids):
            _ip_detail(data, ids[idx])
        else:
            _ip_add(data)

def _ip_detail(data, ip_id):
    ips = data['ips']
    e   = ips[ip_id]
    while True:
        ref = sum(1 for en in data['entries'] if en['ip'] == ip_id)
        r   = menu(ip_label(e), [t('edit'), t('delete')],
                   subtitle=[t('ref_count', n=ref)])
        if r is None:
            return
        if r[0] == 0:
            raw_ip = ask(t('prompt_ip_keep', current=e['ip']), allow_empty=True)
            if raw_ip is None:
                continue
            new_ip = raw_ip or e['ip']
            raw_name = ask(t('prompt_name_keep', current=e.get('name') or t('none_value')),
                           allow_empty=True)
            if raw_name is None:
                continue
            new_name = raw_name or e.get('name', '')
            if new_ip != e['ip'] and any(v['ip'] == new_ip for k, v in ips.items() if k != ip_id):
                notify(t('err_ip_exists', ip=new_ip))
            else:
                e['ip'] = new_ip
                e['name'] = new_name
                save(data)
                notify(t('ok_updated'))
        else:
            sub = [t('will_delete_entries', n=ref)] if ref else None
            if confirm(t('confirm_delete_ip', ip=e['ip']), subtitle=sub):
                data['entries'] = [en for en in data['entries'] if en['ip'] != ip_id]
                del ips[ip_id]
                save(data)
                notify(t('ok_deleted'))
                return

def _ip_add(data):
    ip = ask(t('prompt_ip'))
    if ip is None:
        return
    if any(v['ip'] == ip for v in data['ips'].values()):
        notify(t('err_ip_exists', ip=ip))
        return
    name = ask(t('prompt_name_optional'), allow_empty=True)
    if name is None:
        return
    nid = _next_id(data['ips'])
    data['ips'][nid] = {'ip': ip, 'name': name}
    save(data)
    notify(t('ok_added_ip', ip=ip))

# ── Host management ───────────────────────────────────────────────────────────

def do_host(data):
    while True:
        hosts = data['hosts']
        ids   = list(hosts.keys())
        items = [hosts[i] for i in ids]
        if ids:
            items.append(SEP)
        items.append(t('add_host'))
        r = menu(t('manage_host'), items)
        if r is None:
            return
        idx = r[0]
        if idx < len(ids):
            _host_detail(data, ids[idx])
        else:
            _host_add(data)

def _host_detail(data, host_id):
    hosts = data['hosts']
    while True:
        hostname = hosts[host_id]
        ref = sum(1 for e in data['entries'] if e['host'] == host_id)
        r   = menu(hostname, [t('rename'), t('delete')],
                   subtitle=[t('ref_count', n=ref)])
        if r is None:
            return
        if r[0] == 0:
            new_name = ask(t('prompt_new_hostname'))
            if new_name is None:
                continue
            if new_name in hosts.values():
                notify(t('err_host_exists', name=new_name))
                continue
            hosts[host_id] = new_name
            save(data)
            notify(t('ok_renamed'))
            return
        else:
            sub = [t('will_delete_entries', n=ref)] if ref else None
            if confirm(t('confirm_delete_host', host=hostname), subtitle=sub):
                data['entries'] = [e for e in data['entries'] if e['host'] != host_id]
                del hosts[host_id]
                save(data)
                notify(t('ok_deleted'))
                return

def _host_add(data):
    name = ask(t('prompt_hostname'))
    if name is None:
        return
    if name in data['hosts'].values():
        notify(t('err_host_exists', name=name))
        return
    nid = _next_id(data['hosts'])
    data['hosts'][nid] = name
    save(data)
    notify(t('ok_added_host', name=name))

# ── language ──────────────────────────────────────────────────────────────────

def do_switch_lang():
    global _lang, _T
    langs  = [('en', 'English'), ('zh', '中文')]
    labels = [('★ ' if code == _lang else '  ') + name for code, name in langs]
    r = menu(t('switch_lang'), labels)
    if r is None:
        return
    code = langs[r[0]][0]
    if code == _lang:
        return
    _lang = code
    if os.path.exists(LANG_FILE):
        with open(LANG_FILE) as f:
            all_langs = yaml.safe_load(f) or {}
        _T = all_langs.get(_lang, all_langs.get('en', {}))
    _save_lang()
    notify(t('ok_lang_changed'))

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    _load_lang()
    data = load()
    while True:
        entries   = data['entries']
        n         = len(entries)
        alias_w  = max((display_width(e.get('alias') or '') for e in entries), default=0)
        host_w   = max((display_width(data['hosts'].get(e['host'], '?')) for e in entries), default=0)
        ip_w     = max((display_width((data['ips'].get(e['ip']) or {}).get('ip', '')) for e in entries), default=0)
        items    = [entry_label(data, e, alias_w, host_w, ip_w) for e in entries]
        items  += [t('add_mapping'), SEP, t('manage_ip'), t('manage_host'), SEP, t('switch_lang')]
        r = menu(t('menu_title'), items, back=t('quit'))
        if r is None:
            sys.stdout.write(CLS)
            print('\n  bye\n')
            sys.exit(0)
        idx, _ = r
        if idx < n:
            _entry_detail(data, idx)
        elif idx == n:        # add mapping
            _entry_add(data)
        elif idx == n + 1:    # manage IP  (SEP skipped in logical index)
            do_ip(data)
        elif idx == n + 2:    # manage Host
            do_host(data)
        else:                 # switch lang  (SEP skipped)
            do_switch_lang()

if __name__ == '__main__':
    main()
