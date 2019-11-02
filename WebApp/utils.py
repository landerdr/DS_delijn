import sys

toolbar_width = 40
loading_percentage = 0
def init_loading():
    # setup toolbar
    sys.stdout.write("[%s]" % (" " * toolbar_width))
    sys.stdout.flush()
    sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['

def progress_loading(i, total):
    global loading_percentage
    progress = int(toolbar_width*i/total)
    for _ in range(progress - loading_percentage):
        # update the bar
        sys.stdout.write("-")
        sys.stdout.flush()
    loading_percentage = progress

def complete_loading():
    global loading_percentage
    loading_percentage = 0
    sys.stdout.write("]\n") # this ends the progress bar