import os
import uuid

# Define the name of the configuration file
CONFIG_FILE = "pc_config.ini"

def get_pc_id():
    """
    Retrieves the unique PC ID from a local configuration file.
    If the file does not exist or is empty, a new UUID is generated and saved.
    """
    print("Retrieving PC ID...")
    # Check if the config file exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            pc_id = f.read().strip()
            # If an ID is found, return it
            if pc_id:
                return pc_id
    
    # If the file doesn't exist or is empty, generate a new UUID
    new_pc_id = str(uuid.uuid4())
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(new_pc_id)
    except IOError as e:
        print(f"Error writing PC ID to config file: {e}")
        # Fallback: if writing fails, return a temporary ID
        return "temp_pc_" + str(uuid.uuid4())
    print(f"Generated new PC ID: {new_pc_id}") 
    return new_pc_id

# Example usage (for testing purposes, not part of the main app flow)
if __name__ == "__main__":
    print(f"Your PC ID: {get_pc_id()}")
    # If you run this file multiple times, the ID should remain the same
