class Node:
	def __init__(self, name, values):
        self.name = name
        self.values = values
        self.collection = {}
    def add(self, name, value):
        if isinstance(value, dict):
            if not self.collection.has_key(name):
                self.collection[name] = []
            self.collection[name].append(Node(name, value))
            return self.collection[name][-1]
        else:
            self.values[name] = value
    def kill(self, name):
        pass
    def render(self):
        pass
    