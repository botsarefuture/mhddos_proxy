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
        return f"Name: {self.name}, URL: {self.url}, Methods: {', '.join(self.methods)}, Port: {self.port}, Status: {self.status}"

    def update(self, name=None, url=None, methods=None, port=None, status=None):
        """Update target properties."""
        if name:
            self.name = name
        if url:
            self.url = url
        if methods:
            self.methods = methods
        if port:
            self.port = port
        if status:
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
        response = requests.get(f"{self.BASE_URL}/targets/{target_id}")
        if response.status_code == 200:
            data = response.json()
            target = Target(target_id, data["name"], data["url"], data["methods"], data["port"], data["status"])
            self.targets[target_id] = target
            return target
        else:
            return None

    def get_all_targets(self):
        """Get all active targets."""
        response = requests.get(f"{self.BASE_URL}/targets")
        if response.status_code == 200:
            targets_data = response.json().get("targets", [])
            for target_data in targets_data:
                target = Target(target_data["_id"], target_data["name"], target_data["url"], target_data["methods"], target_data["port"], target_data["status"])
                self.targets[target.target_id] = target
            return list(self.targets.values())
        else:
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
        response = requests.post(f"{self.BASE_URL}/targets", json=data)
        if response.status_code == 201:
            new_target_data = response.json()
            new_target = Target(new_target_data["_id"], new_target_data["name"], new_target_data["url"], new_target_data["methods"], new_target_data["port"], new_target_data["status"])
            self.targets[new_target.target_id] = new_target
            return new_target
        else:
            return None

    def update_target(self, target_id, name=None, url=None, methods=None, port=None, status=None):
        """Update an existing target."""
        target = self.targets.get(target_id)
        if target:
            data = target.to_dict()
            if name:
                data["name"] = name
            if url:
                data["url"] = url
            if methods:
                data["methods"] = methods
            if port:
                data["port"] = port
            if status:
                data["status"] = status
            response = requests.put(f"{self.BASE_URL}/targets/{target_id}", json=data)
            if response.status_code == 200:
                target.update(name, url, methods, port, status)
                return target
        return None

    def delete_target(self, target_id):
        """Delete a specific target."""
        response = requests.delete(f"{self.BASE_URL}/targets/{target_id}")
        if response.status_code == 200:
            del self.targets[target_id]
            return True
        else:
            return False

    def delete_all_targets(self):
        """Delete all targets."""
        response = requests.delete(f"{self.BASE_URL}/targets/all")
        if response.status_code == 200:
            self.targets.clear()
            return True
        else:
            return False
