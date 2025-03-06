import subprocess
import os
import webbrowser

def run_command(command):
    subprocess.run(command, shell=True, check=True)

def open_browser(url):
    chrome_path=r"C:/Program Files/Google/Chrome/Application/chrome.exe"
    webbrowser.get(chrome_path).open(url)

def main():
    # Change directory to your Flask app directory
    os.chdir(r"/mnt/c/Users/santt/Desktop/CustomsPortal_App/st_frontend")

    # Activate the virtual environment
    run_command("bash -c 'source ~/.CustomsPortal/bin/activate && streamlit run app.py'")

    open_browser("http://localhost:8501/")

if __name__ == "__main__":
    main()
