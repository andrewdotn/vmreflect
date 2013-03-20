import random
import string

sysrandom = random.SystemRandom()

def get_random_string(length=20, alphabet=string.letters + string.digits):
    return ''.join(sysrandom.choice(alphabet) for x in range(length))
