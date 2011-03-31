import pyglet
from random import randint
from functools import wraps

from pieces import Piece, pieces

GRID_WIDTH = 10
GRID_HEIGHT = 22
GRID_HIDDEN_ROWS = 2

MOVE_LEFT_KEY = pyglet.window.key.LEFT
MOVE_RIGHT_KEY = pyglet.window.key.RIGHT
ROTATE_CW_KEY = pyglet.window.key.UP

def random_piece():
    index = randint(0, len(pieces) - 1)
    shape = pieces[index]['shape']
    x = GRID_WIDTH//2 - len(shape[0])//2
    y = GRID_HEIGHT - len(shape)
    return Piece(x, y, index)

def yield_i(i):
    while 1:
        yield i

def capture_delta(fn):
    """
    Defines a decorator for use in the DisappearTheBlocks class
    The game state is saved before calling the wrapped function,
    and compared with the state after calling the wrapped function.
    The differences are added to the delta list, used in rendering
    the game
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        piece = set(self.current_piece.get_coords())
        old_state = piece.union(set(self.blocks.keys()))

        ret = fn(self, *args, **kwargs)

        piece = set(self.current_piece.get_coords())
        new_state = piece.union(set(self.blocks.keys()))
        now_empty = old_state.difference(new_state)
        new_blocks = new_state.difference(old_state)

        self.delta.extend(zip(now_empty, yield_i(-1)))
        self.delta.extend(zip(new_blocks, yield_i(self.current_piece.index)))
        return ret
    return wrapper

class DisappearTheBlocks(object):
    """
    Implements a game of te... DisappearTheBlocks
    """
    delta = []
    blocks = {}
    last_action = 0

    def start(self):
        self.current_piece = random_piece()
        self.delta.extend(zip(self.current_piece.get_coords(),
                              yield_i(self.current_piece.index)))
        pyglet.clock.schedule_interval(self.tick, 0.5)

    def valid(self):
        if self.current_piece.y < 0 or self.current_piece.x < 0 \
                or (self.current_piece.x + self.current_piece.width > GRID_WIDTH):
            print self.current_piece.width
            return False
        
        return not (set(self.current_piece.get_coords()) and \
            set(self.blocks.keys()))

    def finish_fall(self):
        print self.current_piece.get_coords()
        self.blocks.update(zip(self.current_piece.get_coords(),
                               yield_i(self.current_piece.index)))
        self.current_piece = random_piece()

    @capture_delta
    def tick(self, dt):
        now = pyglet.clock.get_default().time()
        self.current_piece.y -= 1
        if not self.valid():
            self.current_piece.y += 1
            if now - self.last_action > 1:
                self.finish_fall()
            return

    @capture_delta
    def move_piece(self, direction):
        self.last_action = pyglet.clock.get_default().time()
        if direction > 0 and \
                self.current_piece.x + len(self.current_piece.shape[0]) < GRID_WIDTH:
            self.current_piece.x += 1
        elif direction < 0 and self.current_piece.x > 0:
            self.current_piece.x -= 1

    @capture_delta
    def rotate_piece(self, direction):
        self.last_action = pyglet.clock.get_default().time()
        self.current_piece.rotate(direction)
        if not self.valid():
            self.current_piece.rotate(-direction)

    @capture_delta
    def drop_piece(self):
        while self.valid():
            self.current_piece.y -= 1
        self.current_piece.y += 1
        self.finish_fall()

    def pop_delta(self):
        d = self.delta
        self.delta = []
        return d

    def _wiggle(self):
        return True

class DisappearTheBlocksView(object):
    """
    """
    def __init__(self, x, y, block_img):
        width = block_img.width
        self.bb_coords = (x-1, y-1,
                          x + width*GRID_WIDTH, y-1,
                          x + width*GRID_WIDTH, y + width*GRID_HEIGHT,
                          x-1, y + width*GRID_HEIGHT)

        self.batch = pyglet.graphics.Batch()

        self.block_grid = {}
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                self.block_grid[(i,j)] = pyglet.sprite.Sprite(block_img,
                                                              batch=self.batch,
                                                              x=x + i*width,
                                                              y=y + j*width)
                self.block_grid[(i,j)].visible = False

    def update(self, delta):
        for (pos, index) in delta:
            if pos[1] >= GRID_HEIGHT-2:
                continue
            sprite = self.block_grid[pos]
            if index == -1:
                sprite.visible = False
            else:
                sprite.visible = True
                sprite.color = pieces[index]['color']

    def draw(self):
        pyglet.gl.glColor3f(1.0, 1.0, 1.0)
        pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP,
                             ('v2i', self.bb_coords))
        self.batch.draw()


class DisappearTheBlocksKeyboardController(object):

    def __init__(self, move_fn, rotate_fn, drop_fn):
        self.mapping = {MOVE_LEFT_KEY: lambda: move_fn(-1),
                        MOVE_RIGHT_KEY: lambda:move_fn(1),
                        ROTATE_CW_KEY: lambda: rotate_fn(1)}

    def on_key_press(self, symbol, modifiers):
        if symbol in self.mapping:
            self.mapping[symbol]()

if __name__ == '__main__':
    window = pyglet.window.Window(800, 600)
    img = pyglet.image.load('block.png')
    print 'loaded'
    game = DisappearTheBlocks()
    view = DisappearTheBlocksView(400-125, 20, img)
    controller = DisappearTheBlocksKeyboardController(game.move_piece,
                                                      game.rotate_piece,
                                                      game.drop_piece)

    @window.event
    def on_draw():
        window.clear()
        view.update(game.pop_delta())
        view.draw()

    window.push_handlers(controller)
    game.start()
    print "running"
    pyglet.app.run()
