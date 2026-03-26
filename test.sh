PYTHONPATH=src python3 -m unittest discover -s src/tests -p "test_*.py" -t src -b
PYTHONPATH=src python3 -m unittest discover -s src/tests -p "*_test.py" -t src -b
PYTHONPATH=src python3 -m unittest discover -s src/modules -p "test_*.py" -t src -b
PYTHONPATH=src python3 -m unittest discover -s src/modules -p "*_test.py" -t src -b
