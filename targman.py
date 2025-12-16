import requests

class Target:
    def __init__(self, target_id, name, url, methods, port, status):
        self.target_id = target_id
        self.name = name
        self.url = url
        self.methods = methods
        self.port = port
        self.status = status

    def __str__(self):
        return (f"ID: {self.target_id}\n"
                f"  Name: {self.name}\n"
                f"  URL: {self.url}\n"
                f"  Methods: {', '.join(self.methods)}\n"
                f"  Port: {self.port}\n"
                f"  Status: {self.status}")

    def update(self, name=None, url=None, methods=None, port=None, status=None):
        """Update target properties."""
        if name is not None:
            self.name = name
        if url is not None:
            self.url = url
        if methods is not None:
            self.methods = methods
        if port is not None:
            self.port = port
        if status is not None:
            self.status = status

    def to_dict(self):
        """Return target data as a dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "methods": self.methods,
            "port": self.port,
            "status": self.status
        }
        
    def __repr__(self):
        """
        Return a detailed string representation of the Target object.
        Useful for debugging or logging.
        """
        return (f"Target(target_id={repr(self.target_id)}, "
                f"name={repr(self.name)}, url={repr(self.url)}, "
                f"methods={repr(self.methods)}, port={repr(self.port)}, "
                f"status={repr(self.status)})")

class TargetManager:
    BASE_URL = "https://femdom.pahkinaryhma.fi/"  # Change to your actual API base URL

    def __init__(self):
        self.targets = {}

    def get_target(self, target_id):
        """Retrieve a specific target by ID."""
        try:
            response = requests.get(f"{self.BASE_URL}/targets/{target_id}")
            response.raise_for_status()
            data = response.json()
            target = Target(target_id, data["name"], data["url"], data["methods"], data["port"], data["status"])
            self.targets[target_id] = target
            return target
        except requests.exceptions.RequestException as e:
            print(f"Error getting target: {e}")
            return None

    def get_all_targets(self):
        """Get all active targets."""
        try:
            response = requests.get(f"{self.BASE_URL}/targets")
            response.raise_for_status()
            print(response.json())
            targets_data = response.json().get("targets", [])
            self.targets.clear()
            for target_data in targets_data:
                target = Target(target_data["_id"], target_data["name"], target_data["url"], target_data["methods"], target_data["port"], target_data["status"])
                self.targets[target.target_id] = target
            return list(self.targets.values())
        except requests.exceptions.RequestException as e:
            print(f"Error getting targets: {e}")
            return []

    def create_target(self, name, url, methods, port, status):
        """Create a new target."""
        data = {
            "name": name,
            "url": url,
            "methods": methods,
            "port": port,
            "status": status
        }
        try:
            response = requests.post(f"{self.BASE_URL}/targets", json=data)
            response.raise_for_status()
            print(response.json())
            new_target_data = response.json()
            new_target = Target(new_target_data["target"]["_id"], new_target_data["name"], new_target_data["url"], new_target_data["methods"], new_target_data["port"], new_target_data["status"])
            self.targets[new_target.target_id] = new_target
            return new_target
        except requests.exceptions.RequestException as e:
            print(f"Error creating target: {e}")
            if e.response:
                print(f"Response: {e.response.text}")
            return None

    def update_target(self, target_id, name=None, url=None, methods=None, port=None, status=None):
        """Update an existing target."""
        target = self.targets.get(target_id)
        if not target:
            target = self.get_target(target_id)

        if target:
            data = target.to_dict()
            if name is not None: data["name"] = name
            if url is not None: data["url"] = url
            if methods is not None: data["methods"] = methods
            if port is not None: data["port"] = port
            if status is not None: data["status"] = status
            
            try:
                response = requests.put(f"{self.BASE_URL}/targets/{target_id}", json=data)
                response.raise_for_status()
                target.update(name, url, methods, port, status)
                return target
            except requests.exceptions.RequestException as e:
                print(f"Error updating target: {e}")
                if e.response:
                    print(f"Response: {e.response.text}")
                return None
        print(f"Target with ID {target_id} not found.")
        return None

    def delete_target(self, target_id):
        """Delete a specific target."""
        try:
            response = requests.delete(f"{self.BASE_URL}/targets/{target_id}")
            response.raise_for_status()
            if target_id in self.targets:
                del self.targets[target_id]
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting target: {e}")
            return False

    def delete_all_targets(self):
        """Delete all targets."""
        try:
            response = requests.delete(f"{self.BASE_URL}/targets/all")
            response.raise_for_status()
            self.targets.clear()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting all targets: {e}")
            if e.response and e.response.status_code in [404, 405]: # Not Found or Method Not Allowed
                print("`DELETE /targets/all` not available. Deleting one by one.")
                all_targets = self.get_all_targets()
                if not all_targets:
                    return True # Nothing to delete
                
                deleted_count = 0
                for target in all_targets:
                    if self.delete_target(target.target_id):
                        deleted_count += 1
                return deleted_count == len(all_targets)
            return False

def display_menu():
    print("\n--- Target Manager ---")
    print("1. List all targets")
    print("2. Add a new target")
    print("3. Delete a target")
    print("4. Delete all targets")
    print("5. Exit")

def main():
    manager = TargetManager()

    while True:
        display_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            targets = manager.get_all_targets()
            if targets:
                print("\n--- All Targets ---")
                for target in targets:
                    print(target)
                    print("-" * 20)
            else:
                print("No targets found or error retrieving them.")

        elif choice == '2':
            print("\n--- Add a New Target ---")
            name = input("Enter name: ")
            url = input("Enter URL: ")
            methods_str = input("Enter methods (comma-separated, e.g., GET,POST): ")
            methods = [m.strip().upper() for m in methods_str.split(',')]
            port_str = input("Enter port: ")
            try:
                port = int(port_str)
            except ValueError:
                print("Invalid port. Please enter a number.")
                continue
            status = input("Enter status (e.g., online): ")
            
            new_target = manager.create_target(name, url, methods, port, status)
            if new_target:
                print("\nTarget created successfully:")
                print(new_target)
            else:
                print("\nFailed to create target.")

        elif choice == '3':
            print("\n--- Delete a Target ---")
            target_id = input("Enter the ID of the target to delete: ")
            if manager.delete_target(target_id):
                print(f"Target with ID '{target_id}' deleted successfully.")
            else:
                print(f"Failed to delete target with ID '{target_id}'. It might not exist.")

        elif choice == '4':
            print("\n--- Delete All Targets ---")
            confirm = input("Are you sure you want to delete all targets? (yes/no): ")
            if confirm.lower() == 'yes':
                if manager.delete_all_targets():
                    print("All targets deleted successfully.")
                else:
                    print("Failed to delete all targets.")
            else:
                print("Operation cancelled.")

        elif choice == '5':
            print("Exiting.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()        

