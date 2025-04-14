#!/usr/bin/env python

n = int(input("How much number input? : "))

building = list(map(int, input().split()))
print("\nbuilding : ", building)

min_build = min(building)
print("\nmin(building) : ", min_build)

min_build_n = min(building) * n
print("\nmin(building) * n : ", min_build_n)

sum_build = sum(building)
print("\nsum(building) : ", sum_build)

result = sum_build - min_build_n
print("\nsum(building) - min(building) * n : ", result)
