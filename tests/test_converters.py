import json

import pandas as pd

from fibrabots.convert import abuseipdb, csv, ipvoid, pulsedive, union, virustotal


def test_abuseipdb_converter(tmp_path):
    source = tmp_path / "abuse.json"
    source.write_text(
        json.dumps(
            [
                {
                    "ip": "1.1.1.1",
                    "abuseipdb_confidence_score": 100,
                    "abuseipdb_total_reports": 10,
                    "abuseipdb_num_distinct_users": 5,
                }
            ]
        ),
        encoding="utf-8",
    )
    target = tmp_path / "abuse.xlsx"
    assert abuseipdb.convert(source, target) == 1
    frame = pd.read_excel(target)
    assert frame.loc[0, "ip"] == "1.1.1.1"


def test_virustotal_converter_flattens_stats(tmp_path):
    source = tmp_path / "vt.json"
    source.write_text(
        json.dumps(
            [
                {
                    "ip": "1.1.1.1",
                    "virustotal_reputation": -1,
                    "virustotal_last_analysis_stats": {
                        "malicious": 2,
                        "suspicious": 1,
                        "undetected": 3,
                        "harmless": 4,
                        "timeout": 0,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    target = tmp_path / "vt.xlsx"
    assert virustotal.convert(source, target) == 1
    frame = pd.read_excel(target)
    assert "timeout" not in frame.columns
    assert frame.loc[0, "malicious"] == 2


def test_ipvoid_converter_skips_invalid(tmp_path):
    (tmp_path / "valid.txt").write_text(
        "IP Address Information\n\nDetections Count\t2/90\nIP Address\t1.1.1.1\n",
        encoding="utf-8",
    )
    (tmp_path / "invalid.txt").write_text("sem dados", encoding="utf-8")
    target = tmp_path / "ipvoid.xlsx"
    assert ipvoid.convert(tmp_path, target) == 1
    frame = pd.read_excel(target)
    assert frame.loc[0, "Detection Count"] == 2


def test_pulsedive_converter_counts_risks(tmp_path):
    (tmp_path / "1_1_1_1.json").write_text(
        json.dumps(
            {
                "indicator": "1.1.1.1",
                "risk_recommended": "medium",
                "riskfactors": [
                    {"risk": "medium"},
                    {"risk": "none"},
                    {"risk": "high"},
                ],
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "pulsedive.xlsx"
    assert pulsedive.convert(tmp_path, target) == 1
    frame = pd.read_excel(target)
    assert frame.loc[0, "amount_risk_pulsedrive"] == 3
    assert frame.loc[0, "medium_pulsedrive"] == 1


def test_union_and_csv(tmp_path):
    pd.DataFrame({"ip": ["1.1.1.1"], "a": [1]}).to_excel(tmp_path / "A.xlsx", index=False)
    pd.DataFrame({"ip": ["1.1.1.1"], "b": [2]}).to_excel(tmp_path / "B.xlsx", index=False)
    total = tmp_path / "Total.xlsx"
    assert union.convert(tmp_path, total) == 1
    csv_path = tmp_path / "Total.csv"
    assert csv.convert(total, csv_path) == 1
    assert csv_path.exists()
