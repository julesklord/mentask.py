import os
import sys
from unittest.mock import patch

# Add src to path just in case
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

try:
    from mentask.tools.analysis_logic import get_git_diff_stat
    print(f"Imported from: {sys.modules['mentask.tools.analysis_logic'].__file__}")

    with patch("mentask.tools.analysis_logic.subprocess.run") as mock_run:
        mock_run.return_value = "Mocked!"
        print("Calling get_git_diff_stat...")
        result = get_git_diff_stat()
        print(f"Result: {result}")
        if mock_run.called:
            print("SUCCESS: Mock was called!")
        else:
            print("FAILURE: Mock was NOT called!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
