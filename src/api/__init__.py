import os
import sys

api_directory = os.path.dirname(os.path.abspath(__file__))
if api_directory not in sys.path:
    sys.path.insert(0, api_directory)
