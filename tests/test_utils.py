from fibrabots.bots.browser import cdp_base_url
from fibrabots.utils import ip_to_filename, merge_records


def test_ip_to_filename_ipv4():
    assert ip_to_filename("8.8.8.8", ".txt") == "8_8_8_8.txt"


def test_ip_to_filename_ipv6():
    assert ip_to_filename("2001:db8::1", ".json") == "2001_db8__1.json"


def test_merge_records_replaces_duplicates():
    merged = merge_records([{"ip": "1.1.1.1", "value": 1}], [{"ip": "1.1.1.1", "value": 2}])
    assert merged == [{"ip": "1.1.1.1", "value": 2}]


def test_cdp_base_url_remove_json_suffix():
    assert cdp_base_url("http://host.docker.internal:9222/json") == (
        "http://host.docker.internal:9222"
    )


def test_cdp_base_url_preserva_url_limpa():
    assert cdp_base_url("http://127.0.0.1:9222") == "http://127.0.0.1:9222"
