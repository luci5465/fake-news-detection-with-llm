import os
import sys
import subprocess
import time

DEFAULT_DATA_DIR = "/home/luci/Desktop/fake_news/data"

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

def list_and_select(directory):
    if not os.path.exists(directory):
        print(f"\n[Error] Directory not found: {directory}")
        input("Press Enter to back...")
        return

    while True:
        os.system('clear')
        print(f"Directory: {directory}\n")
        
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

def run_automatic_mode(base_dir):
    os.system('clear')
    print("--- Automatic Pipeline ---")
    
    # Step 1: Crawling
    print("\n[Step 1/5] Crawling")
    ans = input("Do you want to run crawlers? (y/n): ").strip().lower()
    
    if ans == 'y':
        crawlers_dir = os.path.join(base_dir, "crawlers")
        files = sorted([f for f in os.listdir(crawlers_dir) if f.endswith('.py') and f != '__init__.py'])
        
        if not files:
            print("No crawlers found.")
        else:
            print("\nAvailable Crawlers:")
            for i, f in enumerate(files, 1):
                print(f"{i}. {f}")
            
            run_all_opt = len(files) + 1
            print(f"{run_all_opt}. Run ALL Sequentially")
            
            selection = input(f"\nSelect option (e.g. 1,2 or {run_all_opt} for all): ").strip()
            
            selected_indices = []
            
            if selection == str(run_all_opt) or selection.lower() == 'all':
                selected_indices = range(len(files))
            else:
                try:
                    parts = selection.split(',')
                    for p in parts:
                        idx = int(p.strip()) - 1
                        if 0 <= idx < len(files):
                            selected_indices.append(idx)
                except:
                    print("Invalid selection. Skipping crawling.")
            
            for idx in selected_indices:
                script = os.path.join(crawlers_dir, files[idx])
                run_script(script, pause=True)

    # Step 2: Cleaning
    print("\n[Step 2/5] Cleaning Data...")
    cleaner_script = os.path.join(base_dir, "parser", "content_cleaner.py")
    run_script(cleaner_script, pause=False)

    # Step 3: Indexing
    print("\n[Step 3/5] Building Index...")
    index_script = os.path.join(base_dir, "index", "index_builder.py")
    run_script(index_script, pause=False)

    # Step 4: Graph
    print("\n[Step 4/5] Building Graph...")
    graph_script = os.path.join(base_dir, "graph", "graph_builder.py")
    run_script(graph_script, pause=False)

    # Step 5: LLM
    print("\n[Step 5/5] Launching Fake News Detector...")
    llm_script = os.path.join(base_dir, "llm", "fake_news_detector.py")
    run_script(llm_script, pause=True)

def main_menu():
    ensure_data_dir()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    crawlers_dir = os.path.join(base_dir, "crawlers")
    parser_dir = os.path.join(base_dir, "parser")
    index_dir = os.path.join(base_dir, "index")
    graph_dir = os.path.join(base_dir, "graph")
    llm_dir = os.path.join(base_dir, "llm")
    
    while True:
        os.system('clear')
        print(f"Data Path: {DEFAULT_DATA_DIR}\n")
        
        print("1. Crawlers")
        print("2. Data Cleaning")
        print("3. Indexing")
        print("4. Graph Analysis")
        print("5. Fake News Detection")
        print("6. Automatic Mode (Pipeline)")
        print("\n0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '0':
            break
            
        elif choice == '1':
            list_and_select(crawlers_dir)
        elif choice == '2':
            list_and_select(parser_dir)
        elif choice == '3':
            list_and_select(index_dir)
        elif choice == '4':
            list_and_select(graph_dir)
        elif choice == '5':
            list_and_select(llm_dir)
        elif choice == '6':
            run_automatic_mode(base_dir)
        else:
            print("Invalid option.")
            time.sleep(0.5)

if __name__ == "__main__":
    main_menu()
