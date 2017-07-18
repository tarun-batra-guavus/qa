from potluck.logging import logger

def find_master(nodes):
    """Find the Master TM node among a list of nodes"""
    logger.warning("DEPRECATED: Use `potluck.nodes.find_master` instead of `lib.node.find_master`")
    for node in nodes:
        if node.isMaster():
            logger.debug("%s is TM Master" % node)
            return node
    else:
        logger.warn("None of the nodes is Master. Assuming first node to be Master")
        return nodes[0]
