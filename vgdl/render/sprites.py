import pygame

from pathlib import Path
import pkg_resources
from collections import defaultdict

sprites_root = Path(pkg_resources.resource_filename('vgdl', 'sprites'))

class SpriteLibrary:
    default_instance = None

    def __init__(self, sprites_path):
        self.sprites_path = Path(sprites_path)
        if not self.sprites_path.exists():
            raise Exception(f'{sprites_path} does not exist')

        self.caches = defaultdict(dict) # type: Dict[float, Dict[str, str]]


    def sprite_path(self, name):
        stem = Path(name).with_suffix('.png')
        sprite_path = self.sprites_path.joinpath(stem)
        return sprite_path


    # def get_sprite(self, name, scale=1):
    #     # We keep a cache for different scales
    #     cache = self.cache[scale]

    #     if name not in scale:
    #         path = self.sprite_path(name)
    #         img = pygame.image.load(str(path))
    #         cache[name] = img

    #     return cache[name]


    def get_sprite_of_size(self, name, block_size):
        cache = self.caches[block_size]

        # TODO this will reload the sprite on resize...
        if name not in cache:
            path = self.sprite_path(name)
            img = pygame.image.load(str(path))
            # This will only work after the display has been initialised
            img = img.convert_alpha()

            if block_size != max(img.get_rect().size):
                img = pygame.transform.smoothscale(img, (block_size, block_size))

            cache[name] = img

        return cache[name]





    def load_all(self):
        # Mostly for debug purposes, don't use this often
        names = [s.relative_to(sprites_root) for s in self.sprites_path.glob('**/*.png')]

        for name in names:
            self.get_sprite(name)


    @classmethod
    def default(cls):
        # Singleton gets instantiated on first call
        if cls.default_instance is None:
            cls.default_instance = SpriteLibrary(sprites_root)
        return cls.default_instance

