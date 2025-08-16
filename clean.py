from huggingface_hub import scan_cache_dir

hf_cache_info = scan_cache_dir()
print(hf_cache_info)

# Show size of each model
for repo in hf_cache_info.repos:
    print(f"{repo.repo_id}: {repo.size_on_disk_str}")