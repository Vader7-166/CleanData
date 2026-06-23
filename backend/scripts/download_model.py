import os
import sys
from huggingface_hub import snapshot_download

def main():
    # Read settings from environment variables or use defaults
    repo_id = os.environ.get("HF_REPO_ID", "duyhung753951/clean-data_vinai_phobert-base-v2")
    local_dir = os.environ.get("MODEL_PATH", "/working")
    token = os.environ.get("HF_TOKEN", None)

    print("==================================================")
    print("Starting Hugging Face Model Downloader")
    print(f"Repository: {repo_id}")
    print(f"Target Directory: {local_dir}")
    if token:
        print("HF_TOKEN: Configured (authenticating with Hugging Face)")
    else:
        print("HF_TOKEN: Not configured (assuming public repository)")
    print("==================================================")

    # Ensure target directory exists
    os.makedirs(local_dir, exist_ok=True)

    try:
        print("Downloading/Checking model files...")
        downloaded_path = snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            token=token
        )
        print(f"\nSuccess! Model files downloaded and verified at: {downloaded_path}")
        
        # List files to verify
        print("\nFiles in model directory:")
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), local_dir)
                print(f" - {rel_path}")
                
    except Exception as e:
        print(f"\n[ERROR] Model download failed: {e}", file=sys.stderr)
        print("Please check:", file=sys.stderr)
        print("  1. Internet connection inside the container.", file=sys.stderr)
        print("  2. Repository name correctness.", file=sys.stderr)
        print("  3. HF_TOKEN if the repository is private.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
