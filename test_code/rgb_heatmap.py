import pygame
import time
import math

def rgb(minimum, maximum, value):
    # Don't want spectrum to wrap fully because that would be confusing for heat map
    x = (5.25 * value) / (maximum + minimum)
    # shift spectrum to start at purple
    x = (x - .25) % 6
    frac, whole = math.modf(x)
    if 0 <= x < 1:
        r = 0
        g = frac * 255
        b = 255
    elif 1 <= x < 2:
        r = 0
        g = 255
        b = (1 - frac) * 255
    elif 2 <= x < 3:
        r = frac * 255
        g = 255
        b = 0
    elif 3 <= x < 4:
        r = 255
        g = (1 - frac) * 255
        b = 0
    elif 4 <= x < 5:
        r = 255
        g = 0
        b = frac * 255
    elif 5 <= x <= 6:
        r = (1 - frac) * 255
        g = 0
        b = 255
    return (round(r), round(g), round(b))

pygame.init()
surface = pygame.display.set_mode((500,500))

for i in range(500):
    color = rgb(0, 500, i)
    pygame.draw.rect(surface, color, pygame.Rect(i, 1, 1, 500))
    pygame.display.flip()
    time.sleep(.01)

time.sleep(5)
