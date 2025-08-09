# Aggregate test entry-point (optional)
from tests.yad2.test_core import run_all_tests as run_yad2


def main():
    ok_yad2 = run_yad2()
    # GIS tests are pytest-style; recommend running with pytest for full suite
    print("Note: GIS tests are designed for pytest. Run: pytest -q")
    return ok_yad2


if __name__ == "__main__":
    main() 