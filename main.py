import os
import sys
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "data")

def ensure_data_dir():
    if not os.path.exists(DEFAULT_DATA_DIR):
        try:
            os.makedirs(DEFAULT_DATA_DIR)
        except OSError:
            pass

def run_script(script_path, pause=True):
    if not os.path.exists(script_path):
        print(f"\n[Error] File not found: {script_path}")
        time.sleep(1)
        return

    print(f"\n>>> Running: {os.path.basename(script_path)}")
    print("-" * 40)
    
    env = os.environ.copy()
    env["PROJECT_DATA_DIR"] = DEFAULT_DATA_DIR
    
    try:
        subprocess.run([sys.executable, script_path], env=env, check=False)
    except KeyboardInterrupt:
        print("\n[!] Interrupted.")
    except Exception as e:
        print(f"\n[Error] {e}")
    
    print("-" * 40)
    if pause:
        input("Press Enter to continue...")
    else:
        time.sleep(1)

def launch_new_window(command, title="Process"):
    print(f"\n🚀 Launching {title}...")
    try:
        
        cmd = f'start powershell -NoExit -Command "{command}"'
        subprocess.Popen(cmd, shell=True)
        print("Done.")
        time.sleep(1)
    except Exception as e:
        print(f"Error launching window: {e}")
        input("Press Enter...")

def list_and_select(directory):
    if not os.path.exists(directory):
        print(f"\n[Error] Directory not found: {directory}")
        input("Press Enter to back...")
        return

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"Directory: {os.path.basename(directory)}\n")
        
        files = sorted([f for f in os.listdir(directory) if f.endswith('.py') and f != '__init__.py'])
        
        if not files:
            print("No Python scripts found.")
            input("Press Enter to back...")
            return

        for i, f in enumerate(files, 1):
            print(f"{i}. {f}")
        
        print("\n0. Back")
        
        choice = input("\nSelect file: ").strip()
        
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                run_script(os.path.join(directory, files[idx]))
            else:
                print("Invalid selection.")
                time.sleep(0.5)
        except ValueError:
            print("Invalid input.")
            time.sleep(0.5)

def main_menu():
    ensure_data_dir()
    
    crawlers_dir = os.path.join(BASE_DIR, "crawlers")
    parser_dir = os.path.join(BASE_DIR, "parser")
    index_dir = os.path.join(BASE_DIR, "index")
    
    llm_dir = os.path.join(BASE_DIR, "llm")
    
    app_path = os.path.join(llm_dir, "app.py")

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"Project Root: {BASE_DIR}")
        print("-" * 40)
        
        print("1. Crawlers       (Data Acquisition)")
        print("2. Parser         (Data Cleaning)")
        print("3. Indexer        (Build Index)")
        print("-" * 40)
        print("4. Start AI Engine (Ollama)")
        print("5. Launch Web UI   (Streamlit)")
        print("-" * 40)
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
            
        elif choice == '1':
            list_and_select(crawlers_dir)
        elif choice == '2':
            list_and_select(parser_dir)
        elif choice == '3':
            list_and_select(index_dir)
            
        elif choice == '4':
            launch_new_window("ollama serve", "AI Engine")
            
        elif choice == '5':
            if os.path.exists(app_path):
                
                launch_new_window(f"streamlit run \\\"{app_path}\\\"", "Web Interface")
            else:
                print(f"\n[Error] app.py not found at: {app_path}")
                input("Press Enter...")
                
        else:
            print("Invalid option.")
            time.sleep(0.5)

if __name__ == "__main__":
    main_menu()
