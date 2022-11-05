from .base import Agent


agents = {
    'human': lambda size, learn: None
}


def agent(cls):
    name = cls.NAME
    if name in agents.keys():
        raise Exception(f'Agent name was already taken: {name}')
    cls.agent_name = name
    agents[name] = cls
    return cls


from .random import RandomAgent
from .value_iteration import ValueIterAgent
