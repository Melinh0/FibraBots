import pandas as pd

from fibrabots.cli import main


def test_convert_csv_returns_success(tmp_path):
    source = tmp_path / "total.xlsx"
    target = tmp_path / "total.csv"
    pd.DataFrame({"ip": ["1.1.1.1"]}).to_excel(source, index=False)
    assert main(["convert", "csv", "--input", str(source), "--output", str(target)]) == 0
    assert target.exists()


def test_missing_input_returns_error(tmp_path):
    assert main(["convert", "csv", "--input", str(tmp_path / "missing.xlsx")]) == 1
