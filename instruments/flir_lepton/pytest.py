from pylepton import Lepton
import numpy as np
import curses
from time import sleep

a = np.ndarray((60, 80, 1), dtype=np.uint16)
#curses.initscr()

with Lepton("/dev/spidev32766.0") as l:

  try:
      while(1):
        #curses.setsyx(0,0)
        l.capture(a, debug_print=False)
    
        for x in range(0,60):
            for y in range(0,80):
        #print(np.array2string(a, formatter={"%5i"}))
                print('{0:5d}'.format(a[x][y][0]), end='')
            print("\n")
        sleep(1)
        
  except Exception as e:
    raise e
  finally:
    pass #curses.reset_shell_mode()