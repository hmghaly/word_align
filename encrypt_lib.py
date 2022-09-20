import random
#https://stackoverflow.com/questions/4273466/reversible-hash-function
def rhash(n,primary0=23,limit_n=50000):
  return "%04x" % (n * primary0 % limit_n)
    #return "%04x" % (n * 23 % 50000)

def un_rhash(h,modinv0=26087,limit_n=50000):
  return int(h, 16) * modinv0 % limit_n
    #return int(h, 16) * 26087 % 50000

def gen_hex(N=10):
  chars = '0123456789abcdef'
  return "".join(random.sample(chars,N))

#https://stackoverflow.com/questions/4798654/modular-multiplicative-inverse-function-in-python/9758173#9758173
#getting modular inverse in case we want to change the limit or primary
def egcd(a, b):
  if a == 0:
    return (b, 0, 1)
  else:
    g, y, x = egcd(b % a, a)
    return (g, x - (b // a) * y, y)

def modinv(a, m): #a is primary, m is the limit number
  g, x, y = egcd(a, m)
  if g != 1:
    raise Exception('modular inverse does not exist')
  else:
    return x % m

# cur_limit_n=50000
# cur_primary=23
# cur_modinv0=modinv(cur_primary, cur_limit_n)
# print("modinv0",cur_modinv0)

# num0=4502
# print("num0",num0)
# r0=rhash(num0)
# print(r0)

# r1=un_rhash(r0)  # un_rhash(rhash(12))
# print(r1)
# random_hex=gen_hex(4)
# print("random_hex", random_hex)