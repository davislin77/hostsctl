import sys, os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))
import hostsctl

@pytest.fixture(autouse=True)
def reset_lang_state():
    orig_lang = hostsctl._lang
    orig_T = dict(hostsctl._T)
    yield
    hostsctl._lang = orig_lang
    hostsctl._T = orig_T
