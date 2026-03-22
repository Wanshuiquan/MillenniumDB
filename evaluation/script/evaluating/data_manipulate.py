import random
import time

import faker
import networkx as nx
from scipy.io import mmread

from .option import DBS_DIR,DATA_DIR


# manipiulate .qm file for youtube
def random_age():
    random.seed(time.time())
    return random.randint(15, 85)


def random_height():
    random.seed(time.time())

    return random.randint(100, 200)


def random_pos():
    random.seed(time.time())
    return random.choice([-1, 1]) * random.randint(1, 85)


def initialize_youtube_graph():
    fake = faker.Faker()
    source = DATA_DIR / "com-Youtube.mtx"
    destination = DATA_DIR / "youtube.qm"
    with open(source, "r") as fp, open(destination, "w") as outfile:
        a = mmread(fp)
        graph = nx.Graph(a)
        for n in graph.nodes:
            line = f"N{n}:person age:{random_age()} name:\"{fake.word()}\" pos_x:{random_pos()} pos_y:{random_pos()} height:{random_height()} status:\"{random.choice(['single', 'married'])}\"\n"
            outfile.write(line)
        for src, dst in graph.edges:
            relation = random.choice(["B", "A"])
            line = f"N{src} -> N{dst}  :{relation}\n"
            outfile.write(line)


#
# if __name__ == "__main__":
#     initialize_youtube_graph()
