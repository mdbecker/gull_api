#!/bin/bash

# First, print the name of the script itself
echo -n "$0 "

# Now print all arguments as they were received
for arg in "$@"
do
    if [[ $arg =~ [[:space:]] ]]; then
        echo -n "\"$arg\" "
    else
        echo -n "$arg "
    fi
done

# Print a newline at the end for neat formatting
echo ""
