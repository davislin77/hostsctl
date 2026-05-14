import pytest
import hostsctl
from hostsctl import menu, SEP

def getch_seq(monkeypatch, keys):
    it = iter(keys)
    monkeypatch.setattr(hostsctl, 'getch', lambda: next(it))

# ── basic navigation ──────────────────────────────────────────────────────────

def test_enter_selects_first(monkeypatch, capsys):
    getch_seq(monkeypatch, ['ENTER'])
    assert menu('T', ['A', 'B'], back=None) == (0, 'A')

def test_down_then_enter(monkeypatch, capsys):
    getch_seq(monkeypatch, ['DOWN', 'ENTER'])
    assert menu('T', ['A', 'B'], back=None) == (1, 'B')

def test_up_wraps_to_last(monkeypatch, capsys):
    getch_seq(monkeypatch, ['UP', 'ENTER'])
    assert menu('T', ['A', 'B'], back=None) == (1, 'B')

def test_down_wraps_to_first(monkeypatch, capsys):
    getch_seq(monkeypatch, ['DOWN', 'DOWN', 'ENTER'])
    assert menu('T', ['A', 'B'], back=None) == (0, 'A')

# ── exit keys ─────────────────────────────────────────────────────────────────

def test_esc_returns_none(monkeypatch, capsys):
    getch_seq(monkeypatch, ['ESC'])
    assert menu('T', ['A']) is None

def test_left_returns_none(monkeypatch, capsys):
    getch_seq(monkeypatch, ['LEFT'])
    assert menu('T', ['A']) is None

def test_q_returns_none(monkeypatch, capsys):
    getch_seq(monkeypatch, ['q'])
    assert menu('T', ['A']) is None

# ── back item ─────────────────────────────────────────────────────────────────

def test_back_item_returns_none(monkeypatch, capsys):
    # default back appended; DOWN from only item lands on back
    getch_seq(monkeypatch, ['DOWN', 'ENTER'])
    assert menu('T', ['A']) is None

# ── SEP ───────────────────────────────────────────────────────────────────────

def test_sep_is_skipped_during_navigation(monkeypatch, capsys):
    # SEP between A and B: DOWN from A skips SEP and lands on B
    getch_seq(monkeypatch, ['DOWN', 'ENTER'])
    assert menu('T', ['A', SEP, 'B'], back=None) == (1, 'B')
