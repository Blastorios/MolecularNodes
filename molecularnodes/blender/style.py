import bpy
from . import nodes


def format_name(name: str):
    return name.lower().replace(' ', '_')


# class StyleNode:
#     def __init__(self, node_group):


class Style:
    def __init__(self, molecule, style='spheres'):
        self.molecule = molecule
        self.style = style
        self.node = nodes.get_style_node(molecule.object)
        self._input_lookup = {}
        self._initialise_attributes()

    def _initialise_attributes(self):
        for input in self.node.inputs:
            if input.type == "GEOMETRY":
                continue
            new_name = format_name(input.name)
            setattr(self, new_name, input.default_value)
            self._input_lookup[new_name] = input

    def __setattr__(self, name, value):
        if hasattr(self, '_input_lookup'):
            if name in self._input_lookup.keys():
                self._input_lookup[name].default_value = value
            else:
                super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def set(self, style):
        self._remove_attributes()
        self.node = nodes.change_style_node(self.molecule.object, style)
        self._initialise_attributes()
        self.style = style

    def _remove_attributes(self):
        for name in list(self._input_lookup.keys()):
            self._input_lookup.pop(name)
            delattr(self, name)
