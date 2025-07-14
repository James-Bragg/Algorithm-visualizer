import math
import pygame
pygame.init()

class GUIVisualInfo:
    # variables for colours
    Black = 42, 58, 118
    White = 255, 255 , 255
    Green = 0, 255, 0
    Blue = 0, 0, 255
    Red = 255, 0, 0
    BackgroundColor = Black

    # gradient which is used to sets colours of the column
    Gradient = [
        (46, 172, 49),
        (10, 142, 192),
        (235, 170, 18)
    ]

    # variable for font and GUI sizes
    Font = pygame.font.SysFont('Arial', 25)
    BFont = pygame.font.SysFont('Arial', 30)
    Margin = 100
    TopBorder = 150

    #sets information about the size and basic elements of the GUI
    def __init__(self, width, height, array):
        self.width = width
        self.height = height

        self.window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Algorithm visualizer")
        self.setList(array)

    # setting list and creating GUI objects to visualize data onto the screen using the min/max values from the array
    def setList(self, array):
        cleaned_array = [int(x) for x in array if x.strip().isdigit()]

        if not cleaned_array:
            raise ValueError("The input array contains no valid numeric values.")

        self.array = cleaned_array
        self.min = min(self.array)
        self.max = max(self.array)

        if self.max == self.min:
            self.DataBlockHeight = 1
        else:
            self.DataBlockHeight = math.floor((self.height - self.TopBorder) / (self.max - self.min))

        self.DataBlockWidth = round((self.width - self.Margin) / len(self.array))
        self.initializeX = self.Margin // 2
   
def main(array, sort):

    active = True
    limit = pygame.time.Clock()

    # passes gui information such as size and array to determine the size of columns
    GUI = GUIVisualInfo(1024, 768, array)

    #setting default variabes 
    sorting = False
    ascending = True
    sortingAlgorithmName = sort
    sortingAlgorithmGenerator = None

    # runs while application is on
    while active:

        limit.tick(60)
        pygame.display.update()

        # tries to run the sorting algorithm if sorting is set to true
        if sorting:
            try:
                next(sortingAlgorithmGenerator)
            except StopIteration:
                sorting = False
        else:
            # else will update the display elements such as order of sorting order
            from draw_algorithms import draw_key
            draw_key.draw(GUI, sortingAlgorithmName, ascending)

        # sets key events on action or key press to interface with the display
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                active = False
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_SPACE and sorting == False:
                sorting = True
                from Sorting_algorthims import bubbleSort, insertionSort, selectionSort
                if sort == "Bubble Sort":
                    sortingAlgorithmGenerator = bubbleSort(GUI, array, sort, ascending)
                elif sort == "Insertion Sort":
                    sortingAlgorithmGenerator = insertionSort(GUI, array, sort, ascending)
                elif sort == "Selection Sort":
                    sortingAlgorithmGenerator = selectionSort(GUI, array, sort, ascending)
            elif event.key == pygame.K_a and not sorting:
                ascending = True
            elif event.key == pygame.K_d and not sorting:
                ascending = False
    
    pygame.quit


