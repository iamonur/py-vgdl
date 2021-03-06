import itertools
import logging
from typing import NewType, Optional, Union, Dict, List, Tuple
from vgdl.ai import AStarWorld
import numpy as np
import pygame
from pygame.math import Vector2

from vgdl.core import VGDLSprite, Action, Resource, Immutable
from vgdl.core import Color
from vgdl.tools import unit_vector
from .constants import *
from .physics import GridPhysics, ContinuousPhysics



__all__ = [
    'SmartChaser',
    'LookupChaser',
    'Bomber',
    'Chaser',
    'Conveyor',
    'ErraticMissile',
    'Fleeing',
    'Flicker',
    'Immovable',
    'Missile',
    'OrientedFlicker',
    'OrientedSprite',
    'Passive',
    'Portal',
    'RandomInertial',
    'RandomMissile',
    'RandomNPC',
    'ResourcePack',
    'SpawnPoint',
    'Spreader',
    'SpriteProducer',
    'WalkJumper',
    'Walker',
]


class Immovable(VGDLSprite):
    """
    A gray square that does not budge. Can potentially die.
    For sprites that cannot die, consider using Immutable.
    """
    color = GRAY
    is_static = True

class Passive(VGDLSprite):
    """ A square that may budge. """
    color = RED

class ResourcePack(Resource):
    """ Can be collected, and in that case adds/increases a progress bar on the collecting sprite.
    Multiple resource packs can refer to the same type of base resource. """
    is_static = True

class Flicker(VGDLSprite):
    """ A square that persists just a few timesteps. """
    color = RED
    limit = 1
    def __init__(self, **kwargs):
        self._age = 0
        VGDLSprite.__init__(self, **kwargs)

    def update(self, game):
        VGDLSprite.update(self, game)

        self._age += 1
        if self._age >= self.limit:
            # game.kill_sprite(self)
            game.destroy_sprite(self)

class Spreader(Flicker):
    """ Spreads to its four canonical neighbor positions, and replicates itself there,
    if these are unoccupied. """
    spreadprob = 1.
    def update(self, game):
        Flicker.update(self, game)
        if self._age == 2:
            for u in BASEDIRS:
                if game.random_generator.random() < self.spreadprob:
                    game.create_sprite(self.name, (self.lastrect.left + u[0] * self.lastrect.size[0],
                                                     self.lastrect.top + u[1] * self.lastrect.size[1]))

class SpriteProducer(VGDLSprite):
    """ Superclass for all sprites that may produce other sprites, of type 'stype'. """
    stype = None

class Portal(SpriteProducer):
    is_static = True
    color = BLUE

class SpawnPoint(SpriteProducer):
    prob = None
    total = None
    color = BLACK
    is_static = True
    def __init__(self, cooldown=1, prob=1, total=None, **kwargs):
        SpriteProducer.__init__(self, **kwargs)
        if prob:
            self.prob = prob
            self.is_stochastic = (prob > 0 and prob < 1)
        if cooldown:
            self.cooldown = cooldown
        if total:
            self.total = total
        self.counter = 0

    def update(self, game):
        if (game.time % self.cooldown == 0 and game.random_generator.random() < self.prob):
            game.create_sprite(self.stype, (self.rect.left, self.rect.top))
            self.counter += 1

        if self.total and self.counter >= self.total:
            game.kill_sprite(self)

class RandomNPC(VGDLSprite):
    """ Chooses randomly from all available actions each step. """
    speed = 1
    is_stochastic = True

    def update(self, game):
        VGDLSprite.update(self, game)
        self.physics.active_movement(self, game.random_generator.choice(BASEDIRS))

class OrientedSprite(VGDLSprite):
    """ A sprite that maintains the current orientation. """
    draw_arrow = False
    orientation = RIGHT

    state_attributes = VGDLSprite.state_attributes + ['orientation']

    def _draw(self, game):
        """ With a triangle that shows the orientation. """
        VGDLSprite._draw(self, game)
        if self.draw_arrow:
            col = (self.color[0], 255 - self.color[1], self.color[2])
            pygame.draw.polygon(game.screen, col, triPoints(self.rect, unit_vector(self.orientation)))

class Conveyor(OrientedSprite):
    """ A static object that used jointly with the 'conveySprite' interaction to move
    other sprites around."""
    is_static = True
    color = BLUE
    strength = 1
    draw_arrow = True

class Missile(OrientedSprite):
    """ A sprite that constantly moves in the same direction. """
    speed = 1

class OrientedFlicker(OrientedSprite, Flicker):
    """ Preserves directionality """
    draw_arrow = True
    speed = 0

class Walker(Missile):
    """ Keep moving in the current horizontal direction. If stopped, pick one randomly. """
    airsteering = False
    is_stochastic = True
    def update(self, game):
        if self.airsteering or self.lastdirection[0] == 0:
            if self.orientation[0] > 0:
                d = 1
            elif self.orientation[0] < 0:
                d = -1
            else:
                d = game.random_generator.choice([-1, 1])
            self.physics.active_movement(self, (d, 0))

            # TODO this doesn't actually work anymore

        Missile.update(self, game)

class WalkJumper(Walker):
    prob = 0.1
    strength = 10
    def update(self, game):
        if self.lastdirection[0] == 0:
            if self.prob < game.random_generator.random():
                self.physics.active_movement(self, (0, -self.strength))
        Walker.update(self, game)

class RandomInertial(OrientedSprite, RandomNPC):
    physicstype = ContinuousPhysics

class RandomMissile(Missile):
    def __init__(self, **kwargs):
        Missile.__init__(self, orientation=game.random_generator.choice(BASEDIRS),
                         speed=game.random_generator.choice([0.1, 0.2, 0.4]), **kwargs)

class ErraticMissile(Missile):
    """ A missile that randomly changes direction from time to time.
    (with probability 'prob' per timestep). """
    def __init__(self, prob=0.1, **kwargs):
        Missile.__init__(self, orientation=game.random_generator.choice(BASEDIRS), **kwargs)
        self.prob = prob
        self.is_stochastic = (prob > 0 and prob < 1)

    def update(self, game):
        Missile.update(self, game)
        if game.random_generator.random() < self.prob:
            self.orientation = game.random_generator.choice(BASEDIRS)

class Bomber(SpawnPoint, Missile):
    color = ORANGE
    is_static = False
    def update(self, game):
        Missile.update(self, game)
        SpawnPoint.update(self, game)

class SmartChaser(RandomNPC):

    stype = None
    fleeing = False

    def _closestTargets(self, game):
        bestd = 1e100
        res = []
        for target in game.get_sprites(self.stype):
            d = self.physics.distance(self.rect, target.rect)
            if d < bestd:
                bestd = d
                res = [target]
            elif d == bestd:
                res.append(target)
        return res

    def _movesToward(self, game, target):
        res = []
        basedist = self.physics.astar_distance(game.levelstring, frm=(self.rect.left, self.rect.top))
        #self.basedirs = [UP,RIGHT,DOWN,LEFT]
        self.basedirs = [RIGHT,UP,LEFT,DOWN]
        for a in self.basedirs:
            r = self.rect.copy()
            r = r.move(a)
            newdist = self.physics.astar_distance(game.levelstring, frm=(r.left, r.top))
            if self.fleeing and basedist < newdist:
                ret = a
            if not self.fleeing and basedist > newdist:
                return [a]
        return [ret]

    def update(self, game):
        VGDLSprite.update(self, game)
        options = []
        for target in self._closestTargets(game):
            options.extend(self._movesToward(game, target))
        if len(options) == 0:
            raise "Cannot move!"
        self.physics.active_movement(self, options[0])#TODO: GONNA LOOK AT THIS

class Chaser(RandomNPC):
    
    """ Pick an action that will move toward the closest sprite of the provided target type. """
    stype = None
    fleeing = False

    def _closestTargets(self, game):
        bestd = 1e100
        res = []
        for target in game.get_sprites(self.stype):
            d = self.physics.distance(self.rect, target.rect)
            if d < bestd:
                bestd = d
                res = [target]
            elif d == bestd:
                res.append(target)
        return res

    def _movesToward(self, game, target):
        """ Find the canonical direction(s) which move toward the target. """
        res = []
        basedist = self.physics.distance(self.rect, target.rect)
        for a in BASEDIRS:
            r = self.rect.copy()
            r = r.move(a)
            newdist = self.physics.distance(r, target.rect)
            if self.fleeing and basedist < newdist:
                res.append(a)
            if not self.fleeing and basedist > newdist:
                res.append(a)
        return res

    def update(self, game):
        VGDLSprite.update(self, game)
        options = []
        for target in self._closestTargets(game):
            options.extend(self._movesToward(game, target))
        if len(options) == 0:
            options = BASEDIRS
        #Directions are now deterministic since we want SPIN and
        elif LEFT in options:
            self.physics.active_movement(self, LEFT)
        elif UP in options:
            self.physics.active_movement(self, UP)
        elif RIGHT in options:
            self.physics.active_movement(self, RIGHT)
        elif DOWN in options:
            self.physics.active_movement(self, DOWN)

class LookupChaser(RandomNPC):
    stype = None
    fleeing = False
    moves = []

    def _closestTargets(self, game):
        bestd = 1e100
        res = []
        for target in game.get_sprites(self.stype):
            d = self.physics.distance(self.rect, target.rect)
            if d < bestd:
                bestd = d
                res = [target]
            elif d == bestd:
                res.append(target)
        return res

    def _wheresWaldo(self, level, Waldo):
        for line_num, line in enumerate(level):
            for cell_num, cell in enumerate(line):
                if cell == Waldo:
                    return [line_num, cell_num]

    def _get_moves_from_map(self, level):
        max_ = 0
        for line in level:
            for cell in line:
                if cell > max_:
                    max_ = cell
        
        for i in range(max_,-1,-1):
            self.moves.append(self._wheresWaldo(level, i))

    def _movesToward(self, game, target):
        if self.moves == []:
            self._get_moves_from_map(self.physics.astar_map(game.levelstring, frm=(self.rect.left, self.rect.top)))
        index = 0
        for i, elem in enumerate(self.moves):
            if elem[1] == self.rect.left and elem[0] == self.rect.top:
                index = i
                break
        frm = self.moves[index]
        to = self.moves[index-1]

        if frm[0] > to[0]:
            return UP
            
        elif frm[0] < to[0]:
            return DOWN

        elif frm[1] > to[1]:
            return LEFT

        elif frm[1] < to [1]:
            return RIGHT
        
        else:
            raise "WUT"

    def update(self, game):
        VGDLSprite.update(self, game)
        options = []
        for target in self._closestTargets(game):
            options.extend([self._movesToward(game, target)])
        if len(options) == 0:
            raise Exception("Cannot move!")
        left = self.rect.left
        top = self.rect.top
        self.physics.active_movement(self, options[0])
        if self.rect.top == top and self.rect.left == left:
            raise "Erroneous moves from the chaser"
        

class Fleeing(Chaser):
    """ Just reversing directions"""
    fleeing = True

class AStarChaser(RandomNPC):

    """ Move towards the character using A* search. """
    stype = None
    fleeing = False
    drawpath = None
    walkableTiles = None
    neighborNodes = None

    def _movesToward(self, game, target):
        """ Find the canonical direction(s) which move toward
            the target. """
        res = []
        basedist = self.physics.distance(self.rect, target.rect)
        for a in BASEDIRS:
            r = self.rect.copy()
            r = r.move(a)
            newdist = self.physics.distance(r, target.rect)
            if self.fleeing and basedist < newdist:
                res.append(a)
            if not self.fleeing and basedist > newdist:
                res.append(a)
        return res

    def _draw(self, game):
        """ With a triangle that shows the orientation. """
        RandomNPC._draw(self, game)

        if self.walkableTiles:
            col = pygame.Color(0, 0, 255, 100)
            for sprite in self.walkableTiles:
                pygame.draw.rect(game.screen, col, sprite.rect)

        if self.neighborNodes:
            col = pygame.Color(0, 255, 255, 80)
            for node in self.neighborNodes:
                pygame.draw.rect(game.screen, col, node.sprite.rect)

        if self.drawpath:
            col = pygame.Color(0, 255, 0, 120)
            for sprite in self.drawpath[1:-1]:
                pygame.draw.rect(game.screen, col, sprite.rect)

    def _setDebugVariables(self, world, path):
        '''
            Sets the variables required for debug drawing of the paths
            resulting from the A-Star search.
            '''

        path_sprites = [node.sprite for node in path]

        self.walkableTiles = world.get_walkable_tiles()
        self.neighborNodes = world.neighbor_nodes_of_sprite(self)
        self.drawpath = path_sprites

    def update(self, game):
        VGDLSprite.update(self, game)

        world = AStarWorld(game)
        path = world.getMoveFor(self)

        # Uncomment below to draw debug paths.
        # self._setDebugVariables(world,path)

        if len(path)>1:
            move = path[1]

            nextX, nextY = world.get_sprite_tile_position(move.sprite)
            nowX, nowY = world.get_sprite_tile_position(self)

            movement = None

            if nowX == nextX:
                if nextY > nowY:
                    movement = DOWN
                else:
                    movement = UP
            else:
                if nextX > nowX:
                    movement = RIGHT
                else:
                    movement = LEFT

        self.physics.active_movement(self, movement)
