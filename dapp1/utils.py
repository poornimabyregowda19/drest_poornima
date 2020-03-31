import random
import string

def randomstring(stringLength = None):
    N = stringLength if stringLength else 12
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(N)])
