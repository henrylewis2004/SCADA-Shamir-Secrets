# Shamir Secret Sharing - splits a secrete and creates shares to reconstruct secret

import secrets

PRIME = 2**521 - 1  # a Mersenne prime, comfortably bigger than a 256-bit secret
mod = 10

#computes a point on the polynomial with x, the share
def create_share(coeffs, x, prime=PRIME):
    share = 0
    for c in reversed(coeffs): #NOTE: uses horner's method, reference in dis?
        share = share * x + c

    return share

#creates a set of random coefficients in the form (secret + ci*X ... + cn*X^k-1)
def create_coeffs(secret_int, k, prime=PRIME):
    coeffs = []
    coeffs.append(secret_int)
    for i in range(1,k):  
        #coeffs[i]=  secrets.randbelow(prime) #maybe add so it can't be zero
        coeffs.append(secrets.SystemRandom().randrange(2,prime))

        
    return coeffs


#creates a list of shares (excludes x=0 as that would just be the secret)
def split_secret(secret_int, n, k):
    share_list = []
    coeffs=create_coeffs(secret_int,k)

    for i in range(1,n+1):
        share_list.append((i,create_share(coeffs, i)))

    return share_list


def recover_secret(shares, prime=PRIME):
    secret = 0
    for share in shares:
        numerator = 1
        denominator = 1
        for xi in shares:
            if share[0]!=xi[0]:
                numerator = ((0-xi[0]) * numerator) % prime
                denominator = ((share[0] - xi[0]) * denominator) % prime

        secret = (secret + (numerator * pow(denominator,-1,prime)) * share[1]) % prime


    return secret


def test():
    secret = 5
    n = 10
    k = 4
    shares = split_secret(secret,n,k)
    rec=recover_secret(shares[3:8])
    print(f"n: {n}\nk:{k}")
    print(f"secret: {secret}\n")
    print(f"recovered secret: {rec}")


test()
