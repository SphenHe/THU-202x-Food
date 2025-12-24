import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Ensure we are in the correct directory so relative paths work
    if getattr(sys, "frozen", False):
        os.chdir(sys._MEIPASS)
        
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("st.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
