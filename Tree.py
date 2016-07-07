from PIL import Image, ImageDraw
from math import ceil, sqrt

colormap = {'a':'red', 'b':'blue', 'c':'green', 'x':'black'}

def tree_draw(d, coord, lst, r=20, h=70, w=50, lw=10):
    """
    r - radius of nodes
    h - height between levels
    w - the horizontal distance between nodes
    lw - the width of the lines between nodes
    """
    x,y = coord

    if len(lst) > 0 and not isinstance(lst,str): # if its a branch

        # draw edges to its children
        for i in xrange(len(lst)):
            xc = x-len(lst)*w/2 + i*w
            d.line( (x,y, xc, y-h), fill="gray", width=lw)

        # Draw the internal node
        d.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0))

        # draw each child
        for i, n in enumerate(lst):
            # print "Recursing", n
            xc = x-len(lst)*w/2 + i*w
            tree_draw(d, (xc,y-h), n, r=r, h=h, w=w) # draw each at their location
    else:
        d.ellipse( (x-r,y-r,x+r,y+r), fill=colormap.get(lst,"black") )

def draw_tree_grid(outfile, trees, sub_size=(500,500)):
    """
    Draw multiple trees in a grid layout
    - sub_size - how much to give to each tree?
    """
    N = len(trees)
    rows, cols = int(ceil(sqrt(N))), int(ceil(sqrt(N))) # layout arrangement

    im = Image.new("RGB", (sub_size[0]*rows,  sub_size[1]*cols), "white")
    draw = ImageDraw.Draw(im)

    for i, t in enumerate(trees):
        xpos = i%cols
        ypos = (i-xpos)/cols
        tree_draw(draw, (xpos*sub_size[0]+sub_size[0]/2, ypos*sub_size[1]+0.9*sub_size[1]), t)
    im.save(outfile)

if __name__ == "__main__":
    draw_tree_grid("o.png", (['a', ['b', 'c']],
                             ['a', 'a', ['b', 'c', ['b', 'a']]]))

