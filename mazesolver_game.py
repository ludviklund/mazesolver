import pygame, sys, random, threading

# Globals

# Sizes etc for the graphical interface
CELL_WIDTH = CELL_HEIGHT = 20
GIRTH = 4
game_running = True

# Variable to control the speed of the animations, and variables for different colors in RGB format
ANIMATION_SPEED = 100
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
RED = (178, 34, 34)

# Stack will be used to carve out the maze, and solution will contain the coordinates for the shortes available path from start to finish
stack = []
solution = []

class Cell:
    """
    Class for an object that's representing a cell in the maze. 
    At intialization these objects are marked as unvisited, with all four walls active. 
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y 
        self.visited = False
        self.walls = {"TOP": True, "RIGHT": True, "BOTTOM": True, "LEFT": True}

    def set_visited(self):
        """If a cell is marked visited, it won't be visited again"""
        self.visited = True

    def get_coords(self):
        """We return as [x,y] coordinate, but 2D arrays use arr[y][x], which can be confusing"""
        return [self.x, self.y]


class Board:
    """Class to create an empty grid object, and fill it with a randomized maze structure of Cell objects."""
    def __init__(self, game_display, cols, rows, start_pos):
        self.cols  = cols
        self.rows  = rows
        self.game_display = game_display
        self.maze  = []
        self.start_pos = start_pos
        self.create_grid()
    
    def create_grid(self):
        """Populate the maze structure with Cells. Amount of cells depends on the number of rows and columns"""
        for i in range(0, self.cols):
            single_row = []
            for j in range(0, self.rows):
                cell = Cell(i, j)
                single_row.append(cell)
            self.maze.append(single_row)

    def create_outlined_rect(self, cell):
        """Create walls for a given cell at coordinate x,y. Each cell needs four different walls, these are drawn dependent on the value of cell.walls"""
        x, y = cell.get_coords()

        if cell.walls["TOP"]:
            pygame.draw.rect(self.game_display, BLACK, [CELL_WIDTH * y, CELL_HEIGHT * x, CELL_WIDTH, GIRTH]) # top horizontal
        if cell.walls["RIGHT"]:
            pygame.draw.rect(self.game_display, BLACK, [CELL_WIDTH * y + CELL_WIDTH, CELL_WIDTH * x, GIRTH, CELL_HEIGHT]) # right vertical
        if cell.walls["BOTTOM"]:
            pygame.draw.rect(self.game_display, BLACK, [CELL_WIDTH * y, CELL_WIDTH * x + CELL_WIDTH, CELL_WIDTH + GIRTH, GIRTH]) # bottom horizontal
        if cell.walls["LEFT"]:
            pygame.draw.rect(self.game_display, BLACK, [CELL_WIDTH * y, CELL_WIDTH * x, GIRTH, CELL_HEIGHT]) # left vertical
    
    def create_solution_dots(self, cell):
        """Create the dots that shows the shortest available path for the solution"""
        x, y = cell.get_coords()
        pygame.draw.rect(self.game_display, RED, [y * CELL_WIDTH + CELL_WIDTH / 2, x * CELL_HEIGHT + CELL_HEIGHT / 2, GIRTH, GIRTH])

    def draw_board(self):
        """
        This is where we draw the graphical elements. Each iteration we clear the board and draw again, because
        every time a cell changes appearance it must be removed so we don't just draw over it.
        If the maze has been fully carved we draw out the solution. 
        """
        self.game_display.fill(YELLOW)
        m = self.maze
        for i in range(len(m)):
            for obj in m[i]:
                pygame.event.pump()
                if obj.visited:
                    self.create_outlined_rect(obj)
                if obj in solution and not game_running:
                    self.create_solution_dots(obj)

    def get_next(self, cell):
        """Return a random cell from available neighbors. Also includes a check to handle edge cases"""
        neighbors = []
        x, y = cell.get_coords()

        if x > 0:
            top = self.maze[x-1][y]
            if not top.visited:
                neighbors.append(top)
        if y < self.rows - 1:
            right = self.maze[x][y+1]
            if not right.visited:
                neighbors.append(right)
        if x < self.cols - 1:
            bottom = self.maze[x+1][y]
            if not bottom.visited:
                neighbors.append(bottom)
        if y > 0:
            left = self.maze[x][y-1]
            if not left.visited:
                neighbors.append(left)

        if neighbors:
            r = int(random.random() * len(neighbors))
            return neighbors[r]
        else:
            return None

    def make_entrance(self, current):
        """If the starting position is on either the first row or column, or the last row or column, remove a wall so we have an "opening" for our maze"""
        x, y = current.get_coords()
        if y == 0:
            current.walls["LEFT"] = False
        elif x == 0:
            current.walls["TOP"] = False
        elif y == len(self.maze) - 1:
            current.walls["BOTTOM"] = False
        elif x == len(self.maze[0]) - 1:
            current.walls["RIGHT"] = False

    def remove_adjacent_walls(self, current, next_cell):
        """Remove adjacent walls between the current cell and the next one"""
        if not next_cell:
            return None

        current_x, current_y = current.get_coords()
        next_x, next_y = next_cell.get_coords()

        offset_x = current_x - next_x # -1 means we going down, 1 means up
        offset_y = current_y - next_y # -1 means we going left, 1 means right

        if offset_x == -1:
            # Going down
            current.walls["BOTTOM"] = next_cell.walls["TOP"] = False
        elif offset_x == 1:
            # Going up
            current.walls["TOP"] = next_cell.walls["BOTTOM"] = False
        elif offset_y == -1:
            # Going right
            current.walls["RIGHT"] = next_cell.walls["LEFT"] = False
        elif offset_y == 1:
            # Going left
            current.walls["LEFT"] = next_cell.walls["RIGHT"] = False

        # return 1 for debugging purposes
        return 1
    
    def init_maze(self):
        """The backbone of the maze. Here we have control over the current cell, the next cell, the stack and the solution"""
        global solution, game_running
        
        if game_running:
            count = 0                                               # Control the animation speed without choking pygame
            endpos = [len(self.maze) - 1, len(self.maze[0]) - 1]    # Always have the goal at bottom right
            self.maze[endpos[0]][endpos[1]].walls["RIGHT"] = False  # Remove the right wall so we have an "exit point"
            start_x = self.start_pos[0]                                  
            start_y = self.start_pos[1] 

            while [start_x, start_y] == endpos:
                # A backup incase the starting position for what ever reason would be the same as the ending position.
                print("Starting position is the same as the ending position.\nChoosing a new starting position at random.")
                start_x = int(random.random() * self.rows)
                start_y = int(random.random() * self.cols) 
                if [start_x, start_y] != endpos:
                    print("The new starting position is ({}, {}).".format(start_x, start_y))
            current = self.maze[start_y][start_x]                             # Set the cell with coordinates matching the start position as random

            # Set first cell as visited, make an entrance and add it to the stack
            current.set_visited()
            self.make_entrance(current)
            stack.append(current)
        
        while stack:
            # This is where the recursive backtracking is happening.
            # Each next cell is determined by chance, where we are given a random cell from the
            # cells available neighbors. This cell gets added to the stack.
            # Whenever there is a cell with no more neighbors, meaning we cant proceed in that direction,
            # we pop out the last value from the stack. If this has any available neighbors, we proceed,
            # if it doesn't we pop out the last value from the stack until we get one with unvisited neighbors
            # OR the stack is empty, in which case we have populated our entire maze.
            count += 1
            if count % ANIMATION_SPEED == 0:
                self.draw_board()
                next_cell = self.get_next(current)
                if current.get_coords() == endpos:
                    # The stack always contains the shortest available path to whichever cell is the last entry.
                    # Because of this, we know that as soon as the current cell is equal to our endposition,
                    # we know that we have the shortest available path in our stack, so we copy this over to the solution
                    # for later use. We also add the current cell, because this has not yet been added to the stack.
                    solution = stack.copy()
                    solution.append(current)
                if next_cell:
                    # If there exists a next cell, we have to remove the walls between the current and the next, 
                    # then we draw the current cell, add it to the stack, mark next cell as visited, and make
                    # next value to our current one.
                    self.remove_adjacent_walls(current, next_cell)
                    stack.append(current)
                    next_cell.set_visited()
                    current = next_cell
                elif stack:
                    # We still have to draw our cell even if there is no next value to be found.
                    current = stack.pop()
                    
            pygame.display.update()

        game_running = False
        self.draw_board()


def main():
    """
    In main we we take input from the user, which we then use
    use to create our maze, and run the needed functions for it to
    behave like we expect it to. 
    """
    rows = cols = start_x = start_y = 0

    print("First enter how many rows and columns you would like.\n"
        "If the maze stops before it's finished, it's because of recursion limits on your OS.\n"
        "It is not recommended to do go above a 70x70 maze.\n"
        "Leave the input fields blank for default values.")

    user_input = input("Enter number of rows and columns seperated by a space: ")
    if user_input:
        user_input = user_input.split(" ")
        rows, cols = [int(x) for x in user_input]
    else:
        rows = cols = 20

    window_height = rows * CELL_HEIGHT + GIRTH
    window_width  = cols * CELL_WIDTH + GIRTH

    while True:
        user_input = input("Enter x and y-coordinate for the starting position, seperated by a space: ")
        if user_input:
            user_input = user_input.split(" ")
            start_x, start_y = [int(x) for x in user_input]
        else:
            start_x = start_y = 0

        if start_x > cols - 1 or start_y > rows - 1:
            print("Starting x and/or y-coordinate can not be greater than specified number of columns or rows, respectively.")
        else:
            break
    
    # Setup pygame and initialize the maze
    pygame.init()
    game_display = pygame.display.set_mode([window_height, window_width])
    clock = pygame.time.Clock()
    maze = Board(game_display, rows, cols, [start_x, start_y])

    while True:
        # Loop needed for pygame. Checks events for user exit, and prints maze
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        maze.init_maze()
        pygame.display.update()


if __name__ == "__main__":
    main()