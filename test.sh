PYTHONPATH=src python3 -m unittest discover -s src/tests -p "test_*.py" -t src
PYTHONPATH=src python3 -m unittest discover -s src/modules -p "test_*.py" -t src
