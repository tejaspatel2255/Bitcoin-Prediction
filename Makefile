# Makefile for Bitcoin AI Prediction App (Windows PowerShell/CMD Compatible)

.PHONY: setup seed train run-api run-ui run-all test

setup:
	pip install -r requirements.txt

seed:
	venv\Scripts\python scripts/seed_data.py

train:
	venv\Scripts\python scripts/train.py

run-api:
	venv\Scripts\python main.py

run-ui:
	venv\Scripts\streamlit run streamlit_app/Home.py

run-all:
	@echo Starting FastAPI and Streamlit concurrent windows...
	start cmd /k "title FastAPI Backend && venv\Scripts\python main.py"
	start cmd /k "title Streamlit Frontend && venv\Scripts\streamlit run streamlit_app/Home.py"

test:
	venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
