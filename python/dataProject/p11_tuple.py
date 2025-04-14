#!/usr/bin/env python

person = ("Kim", 24, "male")
print(person)

a = ()
print(a)

b = (person, )
print(b)

name, age, gerder = person
print("name :", name)
print("age :", age)
print("gerder :", gerder)

n = 1
numbers = [1, 2]

print(type(person))
print(type(n))
print(type(numbers))

print(person[0])
print(person[-1])

fruit = ("apple", ("banana", "cherry"), ("strawberry", "watermelon"))
print(fruit)
print(fruit[0])
print(fruit[1])
print(fruit[1][0])
print(fruit[1][1])
print(fruit[2][0])
print(fruit[2][1])