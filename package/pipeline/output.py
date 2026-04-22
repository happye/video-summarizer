import os

def write_output(summary, mode):
    """Write summary to Markdown file"""
    print("Writing output to Markdown file...")
    
    # Import OUTPUT_PATH after setting paths
    from config import OUTPUT_PATH
    print(f"OUTPUT_PATH: {OUTPUT_PATH}")
    
    # Ensure the directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created directory: {output_dir}")
    
    # Create Markdown content
    markdown_content = f"""# Video Summary

## Key Points

{summary}

## Summary Mode

{mode}
"""
    
    # Write to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print(f"Output written to {OUTPUT_PATH} successfully!")
