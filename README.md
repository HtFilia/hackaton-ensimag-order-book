# Hackathon Order Book Challenge

Welcome to the Order Book Hackathon! Your goal is to build a high-performance, deterministic order book engine that evolves through increasingly complex levels.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- virtualenv (recommended)

### 2. Setup Environment
Clone the repository and set up your virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/MacOS
# OR
.\venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

## 🏆 Participation Guide

### 1. Register Your Team
Before writing code, register your team by adding an entry to `config/teams.yaml`:

```yaml
teams:
  - id: your_team_name
    members:
      - "Member 1 Name"
      - "Member 2 Name"
```

### 2. Directory Structure
You will work primarily in the `submissions/` directory. Create a folder for your team if it doesn't exist:

```
submissions/
└── your_team_name/
    ├── __init__.py
    ├── level1.py
    └── level2.py
```

*Check `submissions/example_team/` for a reference implementation.*

### 3. The Challenge Levels
The challenge is divided into levels. You must pass validation for the current level to proceed.

*   **Level 1**: Basic Limit Order Book. Support for adding and matching limit orders.
*   **Level 2**: Market Orders. Immediate execution against the book.
*   *(More levels will be revealed as you progress)*

### 4. Workflow
1.  **Implement**: Write your solution for the current level in `submissions/<your_team_name>/levelX.py`.
2.  **Validate**: Run the tests locally to ensure your implementation is correct.
3.  **Submit**: Commit and push your changes. CI will run the validation suite and update the leaderboard.

## 🧪 Running Tests

We use `pytest` for validation. You can run tests for a specific level or generally.

**Run validation for Level 1:**
```bash
pytest tests/levels/test_level1_validation.py
```

**Run all tests:**
```bash
pytest
```

**Development Tip**: You can also write your own tests or run your code manually using the fixtures provided in `tests/fixtures/`.

## 📜 Rules & Guidelines

1.  **Determinism**: Your order book must be deterministic. Given the same sequence of inputs, the final state of the book must always be identical. Avoid using random seeds or system time that affects processing logic.
2.  **Performance**: Efficiency matters!
3.  **No Secrets**: Do not commit API keys or secrets.
4.  **Code Style**: We recommend following PEP 8. formatted code is easier to debug!

## ❓ Troubleshooting

If validation fails:
- Check the error message in the test output.
- Ensure your implementation handles edge cases (e.g., matching multiple orders, partial fills).
- Compare against `submissions/example_team` if you are stuck (but don't just copy-paste!).

Good luck, and may the best engine win! 🚀
