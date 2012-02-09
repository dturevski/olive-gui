STARTTAG, ENDTAG = "<!--%s-->", "<!--/%s-->"
SCALAR = "{{%s}}"

class Node:
	def __init__(self, name, values):
        self.name = name
        self.values = values
        self.collection = {}
        self.template = ''
        
    def add(self, name, value):
        if isinstance(value, dict):
            if not self.collection.has_key(name):
                self.collection[name] = []
            self.collection[name].append(Node(name, value))
            return self.collection[name][-1]
        else:
            self.values[name] = value

    def kill(self, name):
        self.collection[name] = []

    def render(self):
        for name in sel.collection.keys():
            for template in Templates(self):
                acc = ''
                for node in self.collection[name]:
                    node.template = template
                    acc = acc + node.render()
                self._put(acc)

        for key in self.values.keys():
            self.template = self.template.replace(SCALAR % key, self.values[key])
            
        return self.template
        
    def _put(self, acc):
        self.template = self.template[0:self.start], acc, self.template[self.end:]
        self.point = self.start + len(acc)


class Templates:
    def __init__(self, node, name):
        self.node, self.name = node, name
        self.node.point = 0
    def __iter__(self):
        return self
    def next(self):
        startTag, endTag = (STARTTAG % self.name), (ENDTAG % self.name) 
        self.node.start = self.node.template.find(startTag, self.node.point)
        if self.node.start != -1:
            self.node.point = self.node.template.find(endTag, self.node.start)
            self.node.end = self.node.point
            return self.node.template[self.node.start+len(startTag):self.node.end - len(endTag)]
        else:
            raise StopIteration
