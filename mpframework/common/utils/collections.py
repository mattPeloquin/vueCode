#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Utility code for working with collections and aggregations
"""


def accumulate_values( accumulator, new ):
    """
    Default aggregation of values based on the type of items
    """
    if not accumulator:
        accumulator = new

    elif new:
        if not isinstance( new, type( accumulator ) ):
            error = "Mixed types in accumulate_values: {} -> {}".format( accumulator, new )
            raise Exception( error )

        if isinstance( new, dict ):
            accumulator.update( new )
        else:
            accumulator += new

    return accumulator
