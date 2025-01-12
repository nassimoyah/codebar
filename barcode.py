class item:
    ##Constructor to initialize car attributes
    def __init__(self, name, code, price):
        self.name = name
        self.code = code
        self.price = price



chips = item("chips",b'26035352',0.15) 

haricos = item("haricos",b'5410153131455',0.5)


print(chips.code)