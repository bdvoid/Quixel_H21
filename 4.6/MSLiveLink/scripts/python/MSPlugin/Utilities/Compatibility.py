import hou


def get_parm(node, *parm_names):
    if node is None:
        return None

    for parm_name in parm_names:
        parm = node.parm(parm_name)
        if parm is not None:
            return parm

    return None


def set_first_available_parm(node, parm_names, value):
    parm = get_parm(node, *parm_names)
    if parm is None:
        return False

    parm.set(value)
    return True


def node_type_exists(category, node_type_name):
    if category is None:
        return False
    return node_type_name in category.nodeTypes()
