import itertools
import logging
from typing import NewType, Optional, Union, Dict, List, Tuple
from math import sqrt
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

import numpy as np

class Node:

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position

def return_path(current_node,maze):
    path = []
    no_rows = len(maze)
    no_columns = len(maze[0])

    result = [[-1 for i in range(no_columns)] for j in range(no_rows)]
    current = current_node
    while current is not None:
        path.append(current.position)
        current = current.parent
        
    path = path[::-1]
    start_value = 0
    
    for i in range(len(path)):
        result[path[i][0]][path[i][1]] = start_value
        start_value += 1
    return result


def search(maze, start, end, cost=1):
    start = [(x) for x in start]
    start.reverse()
    end = [(x) for x in end]
    

    start_node = Node(None, tuple(start))
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, tuple(end))
    end_node.g = end_node.h = end_node.f = 0

    yet_to_visit_list = []  
    
    visited_list = [] 
    
    yet_to_visit_list.append(start_node)
    
    outer_iterations = 0
    max_iterations = (len(maze) // 2) ** 10
    
    move  =  [[-1, 0 ], # go up
              [ 0, -1], # go left
              [ 1, 0 ], # go down
              [ 0, 1 ]] # go right

    no_rows = len(maze)
    no_columns = len(maze[0])
    
    while len(yet_to_visit_list) > 0:
        
        outer_iterations += 1    

        current_node = yet_to_visit_list[0]
        current_index = 0
        for index, item in enumerate(yet_to_visit_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index
                
        if outer_iterations > max_iterations:
            print ("giving up on pathfinding too many iterations")
            return return_path(current_node,maze)

        yet_to_visit_list.pop(current_index)
        visited_list.append(current_node)

        if current_node == end_node:
            return return_path(current_node,maze)

        children = []

        for new_position in move: 

            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            if (node_position[0] > (no_rows - 1) or 
                node_position[0] < 0 or 
                node_position[1] > (no_columns -1) or 
                node_position[1] < 0):
                continue

            if maze[node_position[0]][node_position[1]] != 0:
                continue

            new_node = Node(current_node, node_position)

            children.append(new_node)

        for child in children:
            
            if len([visited_child for visited_child in visited_list if visited_child == child]) > 0:
                continue

            child.g = current_node.g + cost
            #
            child.h = sqrt(((child.position[0] - end_node.position[0]) ** 2) + 
                       ((child.position[1] - end_node.position[1]) ** 2))

            child.f = child.g + child.h

            if len([i for i in yet_to_visit_list if child == i and child.g > i.g]) > 0:
                continue

            yet_to_visit_list.append(child)

def astartwo(li):
    ret = 0
    for line in li:
        for cell in line:
            if cell > ret:
                ret = cell
#    print(ret)
    return ret

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

<<<<<<< HEAD
=======
    def astar_distance(self, level, frm=(0,0)):
        #level = level.replace("E","0")
        #level = level.replace("A","0")
        level = level.split("\n")
        level = level[:-1]
        #Change it to a 2D array
        for linenum, line in enumerate(level):
            line = list(line)
            
            for cellnum, cell in enumerate(line):
                
                if cell == 'G':
                    to = (linenum, cellnum)
                    cell = '0'

                if cell == 'E':
                    cell = '0'

                if cell == 'A':
                    cell = '0'

                line[cellnum] = int(cell)

            level[linenum] =line
        try:
            if level[frm[1]][frm[0]] == 1:
                return 10000
        except:
            return 10000
        asd = astartwo(search(level, frm, to))
        #print(asd)
        return asd



>>>>>>> bd0b1135d58fe58b6c1ba2cbbb668fe9f2451e2b

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



