import types
import yaml
import hostsctl
from hostsctl import load, save

# ── load / save ───────────────────────────────────────────────────────────────

def test_load_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(hostsctl, 'DATA_FILE', str(tmp_path / 'nonexistent.yaml'))
    assert load() == {'entries': [], 'ips': {}, 'hosts': {}}

def test_load_save_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(hostsctl, 'DATA_FILE', str(tmp_path / 'data.yaml'))
    monkeypatch.setattr(hostsctl, '_write_hosts', lambda d: None)

    original = {
        'entries': [{'alias': 'FooBar工程', 'ip': 1, 'host': 1}],
        'ips':     {1: {'ip': '127.0.0.1', 'name': '本機'}},
        'hosts':   {1: 'foo.bar.com'},
    }
    save(original)
    assert load() == original

# ── _next_id ──────────────────────────────────────────────────────────────────

def test_next_id_empty():
    assert hostsctl._next_id({}) == 1

def test_next_id_with_keys():
    assert hostsctl._next_id({1: 'a', 3: 'b'}) == 4

def test_next_id_ignores_non_int_keys():
    assert hostsctl._next_id({'x': 'a', 2: 'b'}) == 3

# ── t (i18n lookup) ───────────────────────────────────────────────────────────

def test_t_missing_key():
    hostsctl._T = {}
    assert hostsctl.t('nonexistent') == 'nonexistent'

def test_t_returns_value():
    hostsctl._T = {'greeting': 'Hello'}
    assert hostsctl.t('greeting') == 'Hello'

def test_t_with_format():
    hostsctl._T = {'msg': 'Hello {name}'}
    assert hostsctl.t('msg', name='World') == 'Hello World'

# ── _load_lang ────────────────────────────────────────────────────────────────

def test_load_lang_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(hostsctl, 'CONFIG_FILE', str(tmp_path / 'config.yaml'))
    monkeypatch.setattr(hostsctl, 'LANG_FILE',   str(tmp_path / 'lang.yaml'))
    hostsctl._load_lang()
    assert hostsctl._lang == 'en'
    assert hostsctl._T == {}

def test_load_lang_reads_from_config(tmp_path, monkeypatch):
    config    = tmp_path / 'config.yaml'
    lang_file = tmp_path / 'lang.yaml'
    config.write_text('lang: zh\n')
    lang_file.write_text('zh:\n  hello: 你好\nen:\n  hello: Hello\n')
    monkeypatch.setattr(hostsctl, 'CONFIG_FILE', str(config))
    monkeypatch.setattr(hostsctl, 'LANG_FILE',   str(lang_file))
    hostsctl._load_lang()
    assert hostsctl._lang == 'zh'
    assert hostsctl._T.get('hello') == '你好'

# ── _save_lang ────────────────────────────────────────────────────────────────

def test_save_lang_creates_file(tmp_path, monkeypatch):
    config = tmp_path / 'config.yaml'
    monkeypatch.setattr(hostsctl, 'CONFIG_FILE', str(config))
    hostsctl._lang = 'zh'
    hostsctl._save_lang()
    with open(config) as f:
        assert yaml.safe_load(f)['lang'] == 'zh'

def test_save_lang_preserves_existing_keys(tmp_path, monkeypatch):
    config = tmp_path / 'config.yaml'
    config.write_text('other_key: value\n')
    monkeypatch.setattr(hostsctl, 'CONFIG_FILE', str(config))
    hostsctl._lang = 'en'
    hostsctl._save_lang()
    with open(config) as f:
        data = yaml.safe_load(f)
    assert data['lang'] == 'en'
    assert data['other_key'] == 'value'

# ── _write_hosts ──────────────────────────────────────────────────────────────

def _fake_run(captured):
    def run(cmd, input=None, capture_output=False):
        captured['content'] = input.decode()
        return types.SimpleNamespace(returncode=0, stderr=b'')
    return run

def test_write_hosts_creates_section(tmp_path, monkeypatch):
    hosts_file = tmp_path / 'hosts'
    hosts_file.write_text('127.0.0.1 localhost\n')
    monkeypatch.setattr(hostsctl, 'HOSTS_FILE', str(hosts_file))
    captured = {}
    monkeypatch.setattr(hostsctl.subprocess, 'run', _fake_run(captured))

    hostsctl._write_hosts({
        'entries': [{'alias': 'local', 'ip': 1, 'host': 1}],
        'ips':     {1: {'ip': '127.0.0.1', 'name': 'home'}},
        'hosts':   {1: 'foo.bar.com'},
    })

    assert hostsctl.MARKER_BEGIN in captured['content']
    assert '127.0.0.1 foo.bar.com  # local' in captured['content']
    assert hostsctl.MARKER_END in captured['content']
    assert '127.0.0.1 localhost' in captured['content']  # original preserved

def test_write_hosts_replaces_existing_section(tmp_path, monkeypatch):
    hosts_file = tmp_path / 'hosts'
    hosts_file.write_text(
        f'127.0.0.1 localhost\n'
        f'{hostsctl.MARKER_BEGIN}\n'
        f'10.0.0.1 old.example.com\n'
        f'{hostsctl.MARKER_END}\n'
    )
    monkeypatch.setattr(hostsctl, 'HOSTS_FILE', str(hosts_file))
    captured = {}
    monkeypatch.setattr(hostsctl.subprocess, 'run', _fake_run(captured))

    hostsctl._write_hosts({
        'entries': [{'alias': 'new', 'ip': 1, 'host': 1}],
        'ips':     {1: {'ip': '192.168.1.1', 'name': 'server'}},
        'hosts':   {1: 'new.example.com'},
    })

    assert '10.0.0.1 old.example.com' not in captured['content']
    assert '192.168.1.1 new.example.com  # new' in captured['content']

def test_write_hosts_hidden_entry_is_commented(tmp_path, monkeypatch):
    hosts_file = tmp_path / 'hosts'
    hosts_file.write_text('')
    monkeypatch.setattr(hostsctl, 'HOSTS_FILE', str(hosts_file))
    captured = {}
    monkeypatch.setattr(hostsctl.subprocess, 'run', _fake_run(captured))

    hostsctl._write_hosts({
        'entries': [{'alias': 'hidden', 'ip': 1, 'host': 1, 'hidden': True}],
        'ips':     {1: {'ip': '127.0.0.1', 'name': 'local'}},
        'hosts':   {1: 'foo.bar.com'},
    })

    assert '# 127.0.0.1 foo.bar.com  # hidden' in captured['content']
