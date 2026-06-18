import hostsctl

LANG = {'current_ip': 'Current IP: {ip}'}


def make_data():
    return {
        'hosts': {1: 'hello-world.test', 2: 'hi-world.test'},
        'ips': {
            1: {'ip': '127.0.0.1',     'name': '本機'},
            2: {'ip': '192.168.12.34',  'name': '將斗雲端'},
        },
        'entries': [{'alias': 'x', 'host': 1, 'ip': 1}],
    }


def _bracket_cols(items):
    return {hostsctl.display_width(i.split('(')[0]) for i in items}

# ── _entry_switch_ip ────────────────────────────────────────────────────────

def test_switch_ip_list_bracket_aligned(monkeypatch):
    hostsctl._T = dict(LANG)
    data  = make_data()
    calls = []

    def fake_menu(title, items, subtitle=None, back=None):
        calls.append({'items': list(items), 'subtitle': subtitle})
        return None

    monkeypatch.setattr(hostsctl, 'menu', fake_menu)
    hostsctl._entry_switch_ip(data, data['entries'][0])
    assert len(_bracket_cols(calls[0]['items'])) == 1


def test_switch_ip_subtitle_colored(monkeypatch):
    hostsctl._T = dict(LANG)
    data  = make_data()
    calls = []

    def fake_menu(title, items, subtitle=None, back=None):
        calls.append({'items': list(items), 'subtitle': subtitle})
        return None

    monkeypatch.setattr(hostsctl, 'menu', fake_menu)
    hostsctl._entry_switch_ip(data, data['entries'][0])
    sub = calls[0]['subtitle']
    assert hostsctl.CYAN in sub
    assert f'{hostsctl.RST}{hostsctl.CYAN}' in sub

# ── _entry_add ──────────────────────────────────────────────────────────────

def test_add_mapping_ip_list_bracket_aligned(monkeypatch):
    hostsctl._T = dict(LANG)
    data    = make_data()
    calls   = []
    returns = iter([(0, 'host'), None])   # 先選 host，再於選 IP 中止

    def fake_menu(title, items, subtitle=None, back=None):
        calls.append(list(items))
        return next(returns)

    monkeypatch.setattr(hostsctl, 'menu', fake_menu)
    monkeypatch.setattr(hostsctl, 'ask', lambda *a, **k: None)
    hostsctl._entry_add(data)
    assert len(_bracket_cols(calls[1])) == 1   # calls[1] = 選 IP 清單
