'''
@author: Andrea Zoppi
'''


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

