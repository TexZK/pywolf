'''
@author: Andrea Zoppi
'''

from .utils import stream_unpack, stream_unpack_array


class Entity(object):

    def __init__(self, pose):
        self.pose = pose

    def think(self):
        pass

    def on_hit(self, entity):
        pass

    def get_sprite(self, eye_pose):
        return None


class Player(Entity):

    def __init__(self, pose, health, ammos, team_index):
        self.pose = pose
        self.health = health
        self.ammos = ammos
        self.team_index = team_index

    def think(self):
        pass  # TODO

    def on_hit(self):
        pass  # TODO

    def get_sprite(self, eye_pose):
        pass  # TODO


class MapHeader(object):

    def __init__(self, plane_offsets, plane_sizes, width, height, name):
        self.plane_offsets = plane_offsets
        self.plane_sizes = plane_sizes
        self.width = width
        self.height = height
        self.name = name

    @classmethod
    def from_stream(cls, data_stream, planes_count=3):
        planes_count = int(planes_count)
        assert planes_count > 0
        plane_offsets = tuple(stream_unpack_array('<L', data_stream, planes_count))
        plane_sizes = tuple(stream_unpack_array('<H', data_stream, planes_count))
        width, height = stream_unpack('<HH', data_stream)
        name = stream_unpack('<16s', data_stream)
        return cls(plane_offsets, plane_sizes, width, height, name)


class Map(object):

    def __init__(self, header, planes, rules):
        pass  # TODO


class Game(object):

    instance = None

    def __init__(self, rules, gamemap):
        self.rules = rules
        self.gamemap = gamemap
        self.entities = {}  # all
        self.players = {}

