import pytest
from hostsctl import display_width, ljust_display, ip_label, entry_label

# ── display_width ─────────────────────────────────────────────────────────────

def test_display_width_ascii():
    assert display_width('hello') == 5

def test_display_width_cjk():
    assert display_width('工程') == 4

def test_display_width_mixed():
    assert display_width('FooBar工程') == 10  # 6 ASCII + 2 CJK x 2

def test_display_width_empty():
    assert display_width('') == 0

# ── ljust_display ─────────────────────────────────────────────────────────────

def test_ljust_display_ascii():
    assert ljust_display('hi', 5) == 'hi   '

def test_ljust_display_cjk():
    assert ljust_display('工程', 8) == '工程    '  # visual width 4, pad to 8

def test_ljust_display_mixed():
    assert ljust_display('FooBar工程', 12) == 'FooBar工程  '  # visual width 10, pad to 12

def test_ljust_display_no_truncate():
    assert ljust_display('hello', 3) == 'hello'

# ── ip_label ──────────────────────────────────────────────────────────────────

def test_ip_label_none():
    assert ip_label(None) == '?'

def test_ip_label_no_name():
    assert ip_label({'ip': '127.0.0.1'}) == '127.0.0.1'

def test_ip_label_with_name():
    assert ip_label({'ip': '127.0.0.1', 'name': '本機'}) == '127.0.0.1  (本機)'

def test_ip_label_alignment():
    w = display_width('192.168.12.34')
    a = ip_label({'ip': '127.0.0.1',    'name': '本機'},   w)
    b = ip_label({'ip': '192.168.12.34', 'name': '將斗雲端'}, w)
    assert display_width(a.split('(')[0]) == display_width(b.split('(')[0])

# ── entry_label alignment regression ─────────────────────────────────────────

@pytest.fixture
def data():
    return {
        'hosts': {1: 'test.owlting.com', 2: 'api-test.owlting.com'},
        'ips': {
            1: {'ip': '127.0.0.1',    'name': '本機'},
            2: {'ip': '192.168.12.34', 'name': '將斗雲端'},
        },
        'entries': [
            {'alias': 'FooBar工程', 'host': 1, 'ip': 1},
            {'alias': 'API proxy',  'host': 2, 'ip': 2},
        ],
    }

def _widths(data):
    entries = data['entries']
    a = max(display_width(e.get('alias') or '') for e in entries)
    h = max(display_width(data['hosts'].get(e['host'], '?')) for e in entries)
    i = max(display_width((data['ips'].get(e['ip']) or {}).get('ip', '')) for e in entries)
    return a, h, i

def test_bracket_alignment(data):
    a, h, i = _widths(data)
    labels = [entry_label(data, e, a, h, i) for e in data['entries']]
    cols = [display_width(l.split(']')[0]) for l in labels]
    assert len(set(cols)) == 1

def test_arrow_alignment(data):
    a, h, i = _widths(data)
    labels = [entry_label(data, e, a, h, i) for e in data['entries']]
    cols = [display_width(l.split('→')[0]) for l in labels]
    assert len(set(cols)) == 1
