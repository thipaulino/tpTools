
class Tp2dDistribute:

    def __init__(self):
        """
        The distribution is given from 0 to 1, or from the given start limit.
        Meaning if the start limit is 0.8, the distribution will return a list from 0.8 to 1,
        divided by the given amount.
        """
        self.amount = 2
        self.start_limit = 0
        self.end_limit = 1

        self.interval = None
        self.parameter_list = []

    def set_amount(self, amount):
        self.amount = amount

    def set_limit_start(self, limit):
        self.start_limit = limit

    def set_limit_end(self, limit):
        self.end_limit = limit

    def get_interval(self):
        parameter = (1 - self.start_limit) - (1 - self.end_limit)
        self.interval = parameter / (self.amount - 1)

        return self.interval

    def get_parameter_list(self):
        self.get_interval()
        self.parameter_list = []

        for n in range(int(self.amount)):
            parameter = (self.interval * n) + self.start_limit
            self.parameter_list.append(parameter)

        return self.parameter_list






