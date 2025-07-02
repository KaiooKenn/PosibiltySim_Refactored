import sys
import os
import matplotlib.pyplot as plt
import pygame as pg
from random import choice
import numpy as np

pg.init()
Info_Object = pg.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = (Info_Object.current_w) * 4 // 5, (Info_Object.current_h) * 4 // 5
FPS = 30

'''
OOP, Amacımız:
- OOP'nin ilkelerine göre haraket ederek gittikçe daha çok benimsemek
'''
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class GridCell:
    def __init__(self, coord, width, height):
        super().__init__()
        self.coord = coord
        self.color = "white"
        self.surface = pg.Surface((width, height))
        self.rect = self.surface.get_rect(topleft=coord)
        self._is_full = False

    def highlight(self):
        if self.rect.collidepoint(pg.mouse.get_pos()):
            self.color = "red"
        else:
            self.color = "white"

    def draw(self, screen):
        self.surface.fill(self.color)
        screen.blit(self.surface, self.rect)
        

class Grid:
    def __init__(self):
        super().__init__()
        self.divide_x, self.divide_y = 1, 1

        self.cell_width = (SCREEN_WIDTH//self.divide_x)
        self.cell_height = (SCREEN_HEIGHT//self.divide_y)

        self.grids = []
        self.grids.append(GridCell((0, 0), self.cell_width, self.cell_height))

    def update(self):
        for grid in self.grids:
            grid.highlight()

    def multiply(self):
        if (SCREEN_WIDTH//self.divide_x) >= (SCREEN_HEIGHT//self.divide_y):
            self.divide_x += 1
        else:
            self.divide_y += 1

        self.cell_width = (SCREEN_WIDTH//self.divide_x)
        self.cell_height = (SCREEN_HEIGHT//self.divide_y)
        
        self.grids.clear()
        for x in range(self.divide_x):
            for y in range(self.divide_y):
                grid_coord = (SCREEN_WIDTH//self.divide_x)*x, (SCREEN_HEIGHT//self.divide_y)*y
                self.grids.append(GridCell(grid_coord, self.cell_width, self.cell_height))


    def draw(self, screen):
        for grid in self.grids:
            grid.draw(screen)

class Glass:
    def __init__(self, grid_center, width, height):
        super().__init__()
        self.image = pg.image.load(resource_path("graphics/glass.png")).convert_alpha()
        self.image = pg.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect(center=grid_center)
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Simulation:
    def __init__(self):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        self.grid = Grid()
        self.glasses = []

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.grid.multiply()
                    self.glasses.clear()

            if event.type == pg.MOUSEBUTTONDOWN:
                self.put_glass()

    def put_glass(self):
        for grid in self.grid.grids:
            if grid.rect.collidepoint(pg.mouse.get_pos()):
                if not grid._is_full:
                    grid._is_full = True
                    if self.grid.cell_width >= self.grid.cell_height:
                        self.glasses.append(Glass(grid.rect.center, self.grid.cell_height, self.grid.cell_height))
                    else:
                        self.glasses.append(Glass(grid.rect.center, self.grid.cell_width, self.grid.cell_width))
    def update(self):
        self.grid.update()

    def draw_objects(self):
        self.grid.draw(self.screen)
        for glass in self.glasses:
            glass.draw(self.screen)
        

    def run(self):
        while self.running:
            self.handle_events()
            self.update()

            # First, clear the screen from the last frame
            self.screen.fill("black") # Or any background color

            self.draw_objects()
            # print("okey")  # It's better to remove this so it doesn't flood your console

            # IMPORTANT: Update the display to show the changes
            pg.display.flip()
            
            # Control the frame rate
            self.clock.tick(FPS)
        pg.quit()
        sys.exit()

if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()