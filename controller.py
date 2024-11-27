"""Controller Class"""

class Controller():
    def __init__(type):
        if type == "arc":
            from arc import Arc
            cont = Arc()
            
        else:
            from archon import Archon
            cont = Archom()
            
        self.controller = cont