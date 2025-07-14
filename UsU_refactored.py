import sys
import os
import matplotlib.pyplot as plt
import pygame as pg
from random import randint, choice
import cv2
import numpy as np
import json

pg.init()
Info_Object = pg.display.Info()

SCREEN_WIDTH, SCREEN_HEIGHT = (Info_Object.current_w) * 4 // 5, (Info_Object.current_h) * 4 // 5
BUTTON_HUD = 50
PICKER_BLANK = 30
DISPLAY_WIDTH, DISPLAY_HEIGHT = (SCREEN_WIDTH - BUTTON_HUD), (SCREEN_HEIGHT - PICKER_BLANK)
FPS = 30

'''
OOP, Amacımız:
- OOP'nin ilkelerine göre haraket ederek gittikçe daha çok benimsemek
'''
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# `def tone_change` KISMI AI TARAFINDAN YAPILMIŞTIR
def tone_change(surface, new_color_rgb):
    """
    Bir yüzeydeki kırmızı tonlarını, L*a*b* renk uzayını kullanarak yeni bir
    hedef renge dönüştürür. Bu yöntem, gri/doygunluğu düşük hedef renklerde
    bile doğru sonuç verir ve orijinal gölgeleri mükemmel şekilde korur.

    :param surface: Rengi değiştirilecek Pygame yüzeyi.
    :param new_color_rgb: Hedef renk (R, G, B) tuple.
    :return: Rengi değiştirilmiş yeni Pygame yüzeyi.
    """
    # 1. Alfa Kanalını ve Orijinal Yüzeyi Koru
    has_alpha = surface.get_flags() & pg.SRCALPHA
    if has_alpha:
        original_surface_copy = surface.copy()

    # 2. Pygame yüzeyini OpenCV formatına (BGR) hazırla
    view = pg.surfarray.pixels3d(surface)
    img_bgr = cv2.cvtColor(view.transpose([1, 0, 2]), cv2.COLOR_RGB2BGR)

    # 3. Kırmızı pikselleri bulmak için HSV ile maske oluştur (HSV bu iş için idealdir)
    hsv_image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([179, 255, 255])
    mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    red_mask = mask1 + mask2

    if not np.any(red_mask):
        return surface.copy()

    # 4. L*a*b* Renk Nakli
    # Kaynak resmi L*a*b* uzayına çevir
    lab_image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

    # Hedef rengi L*a*b* uzayına çevirip a* ve b* kanallarını al
    target_rgb_u8 = np.uint8([[new_color_rgb]])
    target_lab = cv2.cvtColor(target_rgb_u8, cv2.COLOR_RGB2LAB)
    target_a = target_lab[0][0][1]
    target_b = target_lab[0][0][2]

    # Maskelenen piksellerin sadece renk kanallarını (a* ve b*) değiştir.
    # L* (parlaklık) kanalına dokunma!
    lab_image[red_mask > 0, 1] = target_a
    lab_image[red_mask > 0, 2] = target_b

    # 5. Tekrar Pygame formatına dönüştür
    final_bgr = cv2.cvtColor(lab_image, cv2.COLOR_LAB2BGR)
    final_rgb = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2RGB)
    
    final_surface = pg.surfarray.make_surface(final_rgb.transpose([1, 0, 2]))

    # 6. Alfa Kanalını Geri Yükle
    if has_alpha:
        # Orijinal kopyanın piksellerini değiştirerek alfayı %100 koru
        pg.surfarray.pixels3d(original_surface_copy)[:] = final_rgb.transpose([1, 0, 2])
        return original_surface_copy
    else:
        return final_surface.convert()
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
            self.color = "firebrick4"
        else:
            self.color = "white"

    def draw(self, screen):
        self.surface.fill(self.color)
        screen.blit(self.surface, self.rect)
        

class Grid:
    def __init__(self):
        super().__init__()
        self.divide_x, self.divide_y = 1, 1

        self.cell_width = (DISPLAY_WIDTH//self.divide_x)
        self.cell_height = (DISPLAY_HEIGHT//self.divide_y)

        self.grids = []
        self.grids.append(GridCell((0, 0), self.cell_width, self.cell_height))

    def update(self):
        for grid in self.grids:
            grid.highlight()

    def multiply(self):
        if (DISPLAY_WIDTH//self.divide_x) >= (DISPLAY_HEIGHT//self.divide_y):
            self.divide_x += 1
        else:
            self.divide_y += 1

        self.cell_width = (DISPLAY_WIDTH//self.divide_x)
        self.cell_height = (DISPLAY_HEIGHT//self.divide_y)
        
        self.grids.clear()
        for x in range(self.divide_x):
            for y in range(self.divide_y):
                grid_coord = (DISPLAY_WIDTH//self.divide_x)*x, (DISPLAY_HEIGHT//self.divide_y)*y
                self.grids.append(GridCell(grid_coord, self.cell_width, self.cell_height))


    def draw(self, screen):
        for grid in self.grids:
            grid.draw(screen)

class Glass:
    def __init__(self, grid):
        super().__init__()
        self.grid = grid  # grid is a GridCell instance
        try:
            # Use the GridCell's rect for size
            self.size = min(self.grid.rect.width, self.grid.rect.height)
        except AttributeError as e:
            print(f"error: {e}")
            self.size = 10  # fallback size
        self.image = pg.image.load(resource_path("graphics/glass.png")).convert_alpha()
        self.image = pg.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect(center=self.grid.rect.center)
        self.paid = False
        self._is_full = False
        
    def update_glass(self, fill: bool = False, color = None):
        try:
            self.size = min(self.grid.rect.width, self.grid.rect.height)
        except AttributeError as e:
            print(f"error: {e}")
        if hasattr(self, 'color'):
            del self.color
        if not fill:
            self.image = pg.image.load(resource_path("graphics/glass.png")).convert_alpha()
            self.image = pg.transform.scale(self.image, (self.size, self.size))
        else:
            self.color = color
            glass_img = pg.transform.scale(pg.image.load(resource_path("graphics/filled_glass.png")), (self.size, self.size))
            self.image = tone_change(glass_img, self.color)

    
    def draw(self, screen):
        screen.blit(self.image, self.rect)
    
class ColorPicker:
    def __init__(self, color, coordinate, surface):
        super().__init__()
        self.color = color
        self.surface = surface
        self.rect = surface.get_rect(topleft= coordinate)
        self.count = 0
        self.shownvalue = 0
        self.font = pg.font.Font(None, 30)
        self.font.set_italic(True)
        self.text_color = self.get_font_color(self.color)
        
    # `def get_font_color` KISMI AI İLE YAPILMIŞTIR.    
    @staticmethod
    def get_font_color(bg_color):
        # If bg_color is a pygame.Color or has r, g, b attributes:
        if hasattr(bg_color, 'r') and hasattr(bg_color, 'g') and hasattr(bg_color, 'b'):
            r, g, b = bg_color.r, bg_color.g, bg_color.b
        # If bg_color is a tuple/list, use only the first three elements
        elif isinstance(bg_color, (tuple, list)):
            r, g, b = bg_color[:3]
        else:
            # Fallback default
            r, g, b = (0, 0, 0)
    
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        # Return black if brightness is high, else white
        return (0, 0, 0) if brightness > 128 else (255, 255, 255)
    
    def add_or_sub_count(self, value, need_mouse, *attrs): # TODO: if you don't need to then get rid of `need_mouse`
        if need_mouse and not self.check_mouse():
            return  # Only update if mouse is over this picker
        for attr in attrs:
            try:
                current = getattr(self, attr)
                setattr(self, attr, max(0, current + value))
            except Exception:
                raise Exception(f"There is no {attr} in self.attrs")  #
            
    def check_mouse(self):
        if self.rect.collidepoint(pg.mouse.get_pos()):
            return True
        return False
        
    def draw(self, surface):
        pg.draw.rect(surface, self.color, self.rect, border_radius=8)
        self.text = self.font.render(str(int(self.shownvalue)), True, self.text_color)
        surface.blit(self.text, self.text.get_rect(center= self.rect.center))
        
        
class ColorPickers:
    def __init__(self, colors):
        super().__init__()
        self.colors = colors
        self.pickers = []
        
    @staticmethod
    def create_random_color(all_colors):
        treshold = 20
        attempts = 0
        while True:
            random_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            # If there are no colors yet, accept immediately
            if not all_colors:
                break
            # Check if random_color is sufficiently different from all existing colors
            is_different = True
            for color in all_colors:
                if (
                    abs(random_color[0] - color[0]) < treshold or
                    abs(random_color[1] - color[1]) < treshold or
                    abs(random_color[2] - color[2]) < treshold
                ):
                    is_different = False
                    break
            if is_different:
                break
            attempts += 1
            if attempts >= 100:
                treshold = max(1, treshold - 5)
                attempts = 0
        return random_color
    
    def count(self, value, need_mouse, attrs):
        for picker in self.pickers:
            picker.add_or_sub_count(value, need_mouse, *attrs)  # Unpack attrs here
    
    def addPicker(self):
        if len(self.colors) == len(self.pickers):
            raise Exception(f"all_colors value doesn't equal to pickers value \n {len(self.colors) = } \n {len(self.pickers) = }")
        counts = [(picker.count, picker.shownvalue) for picker in self.pickers]
        self.pickers.clear()
        picker_count = len(self.colors)
        if picker_count == 0:
            return
        picker_width = DISPLAY_WIDTH // picker_count
        for i, color in enumerate(self.colors):
            self.pickers.append(ColorPicker(color, (picker_width * i, DISPLAY_HEIGHT), 
                                            pg.Surface((picker_width, PICKER_BLANK))))
            
        
            if counts and i != picker_count - 1:
                count, shownvalue = counts[i]
                self.pickers[-1].count = count
                self.pickers[-1].shownvalue = shownvalue
            
    def subPicker(self):
        self.pickers.pop()
        
    def color_pick(self):
        for picker in self.pickers:
            if picker.check_mouse() and picker.shownvalue > 0:
                if not hasattr(self, "_picked_color"):
                    self._picked_color = picker.color
            
    def draw(self, surface):
        if self.pickers != []:        
            for picker in self.pickers:
                picker.draw(surface)
             
class Button:
    def __init__(self, surface, coordinate, buttontype = "trash_bin"):
        self.surface = surface
        self.rect = self.surface.get_rect(topleft = coordinate)
        self.color = 'azure2'
        self.buttontype = buttontype
        try:
            self.icon = pg.transform.scale(pg.image.load(f"graphics/icons/{self.buttontype}.png"),
                                        (BUTTON_HUD, BUTTON_HUD))
        except:
            raise(f"Aranan nesne bulunamadı \n {buttontype}")
        
    def highlight(self):
        if self.rect.collidepoint(pg.mouse.get_pos()):
            self.color = 'azure3'
        else:
            self.color = 'azure2'
            
    def get_buttontype(self):
        if self.rect.collidepoint(pg.mouse.get_pos()):
            return self.buttontype
        return False
            
    def draw(self, surface):
        pg.draw.rect(surface, self.color, self.rect, border_radius=8)
        surface.blit(self.icon, self.icon.get_rect(center = self.rect.center))
            
class Buttons:
    def __init__(self):
        self.button_count = 6
        surface = pg.Surface((BUTTON_HUD, SCREEN_HEIGHT//self.button_count))
        coordinates = []
        buttontypes = ["trash_bin", "unfill", "random_one",
                       "random_all", "graphic0", "graphic1"]
        for a in range(self.button_count):
            coordinate = (DISPLAY_WIDTH, (SCREEN_HEIGHT//self.button_count)*a)
            coordinates.append(coordinate)
        self.buttons = [Button(surface, coordinates[a], buttontype=buttontypes[a]) for a in range(self.button_count)]
            
    def update(self):
        for button in self.buttons:
            button.highlight()
    
    def get_buttontype(self):
        for button in self.buttons:
            if button.get_buttontype():
                print(button.get_buttontype())
                return button.get_buttontype()
            
    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)
            
class Simulation:
    def __init__(self):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        self.all_colors = []
        cursor_image = pg.transform.scale(pg.image.load(resource_path("graphics/color_cursor.png")), (37, 55))
        cursor = pg.cursors.Cursor((0, 0), cursor_image)
        pg.mouse.set_cursor(cursor)
        self.picked_color = None
        self.colorPickers = ColorPickers(self.all_colors)
        self.grid = Grid()
        self.buttons = Buttons()
        self.glasses = []
        
        with open('colorValues.json', 'r', encoding='utf-8') as f:
            self.named_colors = json.load(f)
        
    def subColor(self):
        for glass in self.glasses:
            if hasattr(glass, "color"):
                if glass.color == self.all_colors[-1]:
                    glass.update_glass()
        self.all_colors.pop()
        self.colorPickers.subPicker()
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.grid.multiply()
                    self.glasses.clear()
                if event.key == pg.K_UP:
                    self.all_colors.append(self.colorPickers.create_random_color(self.all_colors))
                    self.colorPickers.addPicker()
                if event.key == pg.K_DOWN:
                    if self.colorPickers.pickers != []:
                        self.subColor()
                if self.colorPickers.pickers != []:
                    if event.key == pg.K_LEFT:
                        self.colorPickers.count(-1, True, ('shownvalue', 'count'))
                    if event.key == pg.K_RIGHT:
                        self.colorPickers.count(+1, True, ('shownvalue', 'count'))
            if event.type == pg.MOUSEBUTTONDOWN:
                self.progress_buttons(self.buttons.get_buttontype())
                self.put_or_update_glass()
                self.colorPickers.color_pick()
                if hasattr(self.colorPickers, "_picked_color"):
                    self.picked_color = self.colorPickers._picked_color
                    del self.colorPickers._picked_color
                    self.coloring_mouse()
                    
    def progress_buttons(self, buttontype):
        if buttontype is None:
            return
        if buttontype == 'trash_bin':
            for grid in self.grid.grids:
                grid._is_full = False
            self.glasses.clear()
        elif buttontype == 'unfill':
            for glass in self.glasses:
                glass.update_glass()
                
        elif 'random' in buttontype:
            one_cycle = False
            if buttontype == 'random_one':
                one_cycle = True
                
            self.handle_random_buttons(one_cycle)
            
        elif buttontype == 'graphic0':
            self.handle_graphic_buttons(False)
            
        elif buttontype == 'graphic1':
            self.handle_graphic_buttons(True)
            
        else:
            raise Exception("There is no buttontype for this")
        
    @staticmethod
    def calculate_distance(rgb1, rgb2):
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        return (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2
        
    def name_colors(self, rgb1):
        min_distance = float('inf')
        name = None
        for color in self.named_colors:
            rgb2 = color['rgb']
            distance = self.calculate_distance(rgb1, rgb2)
            
            if distance < min_distance:
                min_distance = distance
                name = color['name']
                
                if distance == 0:
                    break
        return name
        
    def handle_graphic_buttons(self, bar):
        # Theoretical probability is based on the total number of items available.
        total_theoretical_count = sum(picker.count for picker in self.colorPickers.pickers)

        # Experimental probability is based on the items that have been "used" or "drawn".
        items_drawn = [picker.count - picker.shownvalue for picker in self.colorPickers.pickers]
        total_experimental_count = sum(items_drawn)

        fig, ax = plt.subplots()

        labels = []
        theoretical_values = []
        experimental_values = []
        for i, picker in enumerate(self.colorPickers.pickers):
            if picker.count > 0:
                labels.append(self.name_colors(picker.color).upper())
                # Calculate theoretical probability
                if total_theoretical_count > 0:
                    theoretical_values.append(picker.count / total_theoretical_count)
                else:
                    theoretical_values.append(0)
                # Calculate experimental probability
                if total_experimental_count > 0:
                    experimental_values.append(items_drawn[i] / total_experimental_count)
                else:
                    experimental_values.append(0)
        if bar:

            # This part creates the bar chart.
            x = np.arange(len(labels))
            width = 0.35  # the width of the bars

            rects1 = ax.bar(x - width/2, theoretical_values, width, label='Teorik', color= 'maroon')
            rects2 = ax.bar(x + width/2, experimental_values, width, label='Deneysel', color = 'cornflowerblue')

            ax.set_ylabel('Probability')
            ax.set_title('Theoretical vs. Experimental Probability')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.legend()

            fig.tight_layout()
            plt.show()
            
        else:
            average_theoretical = sum(theoretical_values)/ len(theoretical_values)
            y_values = []
            x_values = [] # how many glasses are calculated
            for i in range(len(experimental_values)):
                if i == 0:
                    x_values.append(items_drawn[i])
                    y_values.append(experimental_values[i])
                else:
                    x_values.append(items_drawn[i] + x_values[i - 1])
                    y_values.append((experimental_values[i] + experimental_values[i - 1])/ i + 1)
            
            ax.axhline(y = average_theoretical, color= 'maroon', label = "Teorik")
            ax.plot(x_values, y_values,
                    color = "cornflowerblue",
                    linestyle = "--",
                    marker = "*",
                    markersize = 15,
                    label = "Deneysel")              
            ax.set_title("Büyük Sayılar Yasası")
            ax.set_ylabel("Olasılık")
            ax.set_xlabel("Doldurulmuş Bardaklar")
            
            ax.legend()
            
            plt.show()
            
                     
    def handle_random_buttons(self, onecycle):
        usable_colors = sorted([picker for picker in self.colorPickers.pickers], key= lambda picker: picker.shownvalue, reverse=True)
        print([picker.shownvalue for picker in usable_colors])
        if usable_colors:
            for grid in self.grid.grids:
                if not grid._is_full:
                    usable_colors = [usable_color for usable_color in usable_colors if usable_color.shownvalue > 0]
                    if not usable_colors:
                        return
                    grid._is_full = True
                    self.glasses.append(Glass(grid))
                    color = choice(usable_colors).color
                    for usable_color in usable_colors:
                        if usable_color.color == color:
                            usable_color.shownvalue -= 1
                    self.glasses[-1].update_glass(fill = True, color = color)
                    if onecycle:
                        break
                    
    def coloring_mouse(self, coloring: bool = True):
        if coloring:
            cursor_image = tone_change(
                pg.transform.scale(pg.image.load(resource_path("graphics/color_cursor.png")), (37, 55)),
                self.picked_color
            )
        else:
            cursor_image = pg.transform.scale(pg.image.load(resource_path("graphics/color_cursor.png")), (37, 55))
            
        cursor = pg.cursors.Cursor((0, 0), cursor_image)
        pg.mouse.set_cursor(cursor)

    def put_or_update_glass(self):
        for grid in self.grid.grids:
            if grid.rect.collidepoint(pg.mouse.get_pos()):
                if not grid._is_full:
                    grid._is_full = True
                    self.glasses.append(Glass(grid))
                else:
                    for glass in self.glasses:
                        if glass.rect.center == grid.rect.center and not glass._is_full and self.picked_color:
                            glass.update_glass(fill=True, color= self.picked_color)
                            self.picked_color = None
                            self.coloring_mouse(False)
                            
    def update_counts(self):
        for color_picker in self.colorPickers.pickers:
            color_used = 0
            for glass in self.glasses:
                if hasattr(glass, 'color'):
                    if color_picker.color == glass.color:
                        color_used += 1
            current = getattr(color_picker, 'count')
            setattr(color_picker, 'shownvalue', current - color_used)
                       
    def update(self):
        self.grid.update()
        self.update_counts()
        self.buttons.update()

    def draw_objects(self):
        self.grid.draw(self.screen)
        for glass in self.glasses:
            glass.draw(self.screen)
        self.colorPickers.draw(self.screen)
        self.buttons.draw(self.screen)
        

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            
            # First, clear the screen from the last frame
            self.screen.fill("blue") # Or any background color

            self.draw_objects()

            # IMPORTANT: Update the display to show the changes
            pg.display.flip()
            
            # Control the frame rate
            self.clock.tick(FPS)
        pg.quit()
        sys.exit()

if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()