from math import exp, log

def logistic(x: float, multiplier=1) -> float:
    """
    Logistic function to normalize values between 0 and 1.
    :param x: input value
    :param multiplier: Changes range from (0, 1) to (0, multiplier)
    :return: normalized value
    """
    return (1 / (1 + exp(-x))) * multiplier


def linear(x: float, multiplier=1, max_value: float = None) -> float:
    """
    Linear normalization function to normalize values between 0 and max_value.
    :param multiplier: Multiplies the output :)
    :param x: input value
    :param max_value: maximum value for normalization
    :return: normalized value
    """
    if max_value is None:
        return x * multiplier
    return min(x, max_value) * multiplier


def exponential(x: float, base: float = 2, multiplier=1, max_value: float = None) -> float:
    """
    Exponential normalization function to normalize values.
    :param x: input value
    :param base: exponential base
    :param multiplier: Multiplies the output :)
    :param max_value: maximum value for normalization
    :return: normalized value
    """
    value = (base ** x) * multiplier
    if max_value is None:
        return value
    return min(value, max_value)


def logarithmic(x: float, base: float = 10, multiplier=1) -> float:
    """
    Logarithmic normalization function to normalize values.
    :param x: input value
    :param base: logarithm base
    :param multiplier: Multiplies the output :)
    :return: normalized value
    """
    if x <= 0:
        return 0
    return log(x, base) * multiplier