import itertools
import logging
from typing import NewType, Optional, Union, Dict, List, Tuple

import numpy as np
import pygame
from pygame.math import Vector2
import collections

from vgdl.core import Action, Physics
from vgdl.ontology.constants import NOOP

__all__ = [
    'GridPhysics',
    'ContinuousPhysics',
    'GravityPhysics'
]

class GridPhysics(Physics):
    """ Define actions and key-mappings for grid-world dynamics. """

    def passive_movement(self, sprite):
        """
        TODO This can be slightly dangerous and should probably be refactored.
        All sprites with an orientation and speed and GridPhysics will automatically
        move in that direction, passively.
        """
        if sprite.speed is None:
            speed = 1
        else:
            speed = sprite.speed
        if speed != 0 and hasattr(sprite, 'orientation'):
            sprite._update_position(sprite.orientation, speed * self.gridsize[0])

    def active_movement(self, sprite, action, speed=None):
        if speed is None:
            if sprite.speed is None:
                speed = 1
            else:
                speed = sprite.speed
        if speed != 0 and action is not None and action != NOOP:
            # TODO have all actions be Action
            if isinstance(action, Action):
                action = action.as_vector()
            sprite._update_position(action, speed * self.gridsize[0])


    def distance(self, r1, r2):
        """ Grid physics use Hamming distances. """
        return (abs(r1.top - r2.top)
                + abs(r1.left - r2.left))

    def new_distance(self, level, wall='1', floor='0', frm=(0,0), goal='G'):

        level = level.replace("E","0")
        level = level.replace("A","0")
        level = level.split("\n")
        level = level[:-1]
        
        width = len(level[0])
        height = len(level)

        if frm[0] > height or frm[1] > width:
            return 10000
        try:
            if level[frm[1]][frm[0]] == wall:
                return 10000
        except:
            return 10000
        queue = collections.deque([[frm]])
        seen = set([frm])
        

        while queue:
            path = queue.popleft()
            x, y = path[-1]
            if level[y][x] == goal:
                if path is None:
                    return 10000
                return len(path)
            for x2, y2 in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
                if 0 <= x2 < width and 0 <= y2 < height and level[y2][x2] != wall and (x2, y2) not in seen:
                    queue.append(path + [(x2, y2)])
                    seen.add((x2, y2))

        return 10000


class ContinuousPhysics(GridPhysics):
    def passive_movement(self, sprite):
        if not hasattr(sprite, 'orientation'):
            return
        # sprite._updatePos(sprite.orientation, sprite.speed)
        # if self.gravity > 0 and sprite.mass > 0:
        #     sprite.passive_force = (0, self.gravity * sprite.mass)
        #     self.activeMovement(sprite, sprite.passive_force)

        if self.gravity > 0 and sprite.mass > 0:
            sprite.passive_force = Vector2(0, self.gravity * sprite.mass)
            self.active_movement(sprite, sprite.passive_force)


    def active_movement(self, sprite, force, speed=None):
        """
        Updates sprite.orientation and sprite.speed, which together make up
        the sprite's velocity.
        """

        # TODO understand how this is now completely different from
        # gridphysics activeMovement, and why I changed it to be so?
        # Might have to grab old schematics.

        if speed is None:
            old_velocity = sprite.velocity
        else:
            old_velocity = sprite.orientation * speed

        force = Vector2(force)
        velocity = old_velocity + force / sprite.mass

        sprite.velocity = velocity


    def distance(self, r1, r2):
        """ Continuous physics use Euclidean distances. """
        return (Vector2(r1.topleft) - Vector2(r2.topleft)).normalize()

class GravityPhysics(ContinuousPhysics):
    gravity = 1



