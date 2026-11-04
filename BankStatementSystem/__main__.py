"""Run the Flask application when executing the top-level package as a module:
    python -m BankStatementSystem
"""

import os
import sys
import socket

pkg_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(pkg_dir)
for p in [parent_dir, pkg_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from BankStatementSystem import create_app


def _find_free_port(start_port: int = 5000, max_port: int = 5100) -> int:
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


chosen_port = _find_free_port(int(os.getenv("PORT", "5000")))
app = create_app()

if __name__ == "__main__":
    print(f"Running Flask app on http://127.0.0.1:{chosen_port}")
    app.run(host="127.0.0.1", port=chosen_port, debug=True)
