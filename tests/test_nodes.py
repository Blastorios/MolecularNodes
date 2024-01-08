import bpy
import pytest
import molecularnodes as mn
from molecularnodes.blender import nodes
import random
import tempfile

from . import utils
from .constants import codes, test_data_directory
random.seed(6)

mn.unregister()
mn.register()

def test_node_name_format():
    assert mn.blender.nodes.format_node_name("MN_style_cartoon") == "Style Cartoon"

def test_get_nodes():
    mol = mn.io.pdb.load('4ozs', style='spheres')
    
    assert nodes.get_nodes_last_output(mol.modifiers['MolecularNodes'].node_group)[0].name == "MN_style_spheres"
    nodes.realize_instances(mol)
    assert nodes.get_nodes_last_output(mol.modifiers['MolecularNodes'].node_group)[0].name == "Realize Instances"
    assert nodes.get_style_node(mol).name == "MN_style_spheres"
    
    mol2 = mn.io.pdb.load('1cd3', style='cartoon', build_assembly=True)
    
    assert nodes.get_nodes_last_output(mol2.modifiers['MolecularNodes'].node_group)[0].name == "MN_assembly_1cd3"
    assert nodes.get_style_node(mol2).name == "MN_style_cartoon"

def test_selection():
    chain_ids = [let for let in 'ABCDEFG123456']
    node = nodes.chain_selection('test_node', chain_ids, label_prefix="Chain ")
    
    input_sockets = nodes.inputs(node)
    for letter, socket in zip(chain_ids, input_sockets.values()):
        assert f"Chain {letter}" == socket.name
        assert socket.default_value is False

with tempfile.TemporaryDirectory() as temp:
    @pytest.mark.parametrize("code", codes)
    @pytest.mark.parametrize("file_format", ['mmtf', 'cif'])
    @pytest.mark.parametrize("attribute", ["chain_id", "entity_id"])
    def test_selection_working(snapshot, attribute, code, file_format):
        mol = mn.io.pdb.load(code, style='ribbon',cache_dir=temp, file_format=file_format)
        group = mol.modifiers['MolecularNodes'].node_group
        node_sel = nodes.add_selection(group, mol.name, mol[f'{attribute}s'], attribute)
        
        n = len(node_sel.inputs)
        
        for i in random.sample(list(range(n)), max(n - 2, 1)):
            node_sel.inputs[i].default_value = True
        
        nodes.realize_instances(mol)
        utils.apply_mods(mol)
        
        snapshot.assert_match(
            utils.sample_attribute_to_string(mol, 'position'), 
            "position.txt"
        )
    
    @pytest.mark.parametrize("code", codes)
    @pytest.mark.parametrize("file_format", ['mmtf', 'cif'])
    @pytest.mark.parametrize("attribute", ["chain_id", "entity_id"])
    def test_color_custom(snapshot, code, file_format, attribute):
        mol = mn.io.pdb.load(code, style='ribbon', file_format = file_format, cache_dir=temp)
        
        group_col = mn.blender.nodes.chain_color(f'MN_color_entity_{mol.name}', input_list=mol[f'{attribute}s'], field = attribute)
        group = mol.modifiers['MolecularNodes'].node_group
        node_col = mn.blender.nodes.add_custom(group, group_col.name, [0, -200])
        group.links.new(node_col.outputs[0], group.nodes['MN_color_set'].inputs['Color'])
        
        snapshot.assert_match(
            utils.sample_attribute_to_string(mol, 'Color', n = 500), 
            'color.txt'
        )


def test_custom_resid_selection():
    node = mn.blender.nodes.resid_multiple_selection('new_node', '1, 5, 10-20, 40-100')
    numbers = [1, 5, 10, 20, 40, 100]
    assert len(nodes.outputs(node)) == 2
    counter = 0
    for item in node.interface.items_tree:
        if item.in_out == "INPUT":
            assert item.default_value == numbers[counter]
            counter += 1

def test_op_custom_color():
    mol = mn.io.local.load(test_data_directory / '1cd3.cif')
    mol.select_set(True)
    group = mn.blender.nodes.chain_color(f'MN_color_chain_{mol.name}', input_list=mol['chain_ids'])
    
    assert group
    assert group.interface.items_tree['Chain G'].name == 'Chain G'
    assert group.interface.items_tree[-1].name == 'Chain G'
    assert group.interface.items_tree[0].name == 'Color'

def test_color_chain(snapshot):
    mol = mn.io.local.load(test_data_directory / '1cd3.cif', style='cartoon')
    group_col = mn.blender.nodes.chain_color(f'MN_color_chain_{mol.name}', input_list=mol['chain_ids'])
    group = mol.modifiers['MolecularNodes'].node_group
    node_col = mn.blender.nodes.add_custom(group, group_col.name, [0, -200])
    group.links.new(node_col.outputs[0], group.nodes['MN_color_set'].inputs['Color'])
    
    utils.apply_mods(mol)
    snapshot.assert_match(
        utils.sample_attribute_to_string(mol, 'Color', n = 500), 
        'color_chain_values.txt'
    )
