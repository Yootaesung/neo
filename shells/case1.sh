#!/bin/bash

a=0

echo -n "Input : "
read a

let a/=10

case "$a" in
    10) echo "A";;
    9) echo "B";;
    8) echo "C";;
    7) echo "D";;
    6) echo "E";;
    *) echo "F";;
esac
echo "Thank you~ Bye~!!"