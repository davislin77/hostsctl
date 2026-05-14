import hostsctl
from hostsctl import load, save

def test_load_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(hostsctl, 'DATA_FILE', str(tmp_path / 'nonexistent.yaml'))
    assert load() == {'entries': [], 'ips': {}, 'hosts': {}}

def test_load_save_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(hostsctl, 'DATA_FILE', str(tmp_path / 'data.yaml'))
    monkeypatch.setattr(hostsctl, '_write_hosts', lambda d: None)  # skip sudo

    original = {
        'entries': [{'alias': 'FooBar工程', 'ip': 1, 'host': 1}],
        'ips':     {1: {'ip': '127.0.0.1', 'name': '本機'}},
        'hosts':   {1: 'foo.bar.com'},
    }
    save(original)
    assert load() == original
