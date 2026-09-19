def calculate_primes_up_to(n:int)->list[int]:
    primes=[]
    for num in range(2,n):
        is_prime=all(num % i !=0 for i in range(2,int(num**0.5)+1))
        if is_prime:
            primes.append(num)
    return primes