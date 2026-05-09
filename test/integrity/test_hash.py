# Test to check if sha512_256 is supported in the hashlib library

import hashlib

try:
    h = hashlib.new('sha512_256')
    print('sha512_256 is supported')
except ValueError:
    print('sha512_256 is not supported')