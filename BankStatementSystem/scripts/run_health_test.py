import os, sys, json
# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from BankStatementSystem import create_app

app = create_app()
with app.test_client() as client:
    response = client.get('/health')
    print(json.dumps(response.get_json()))
