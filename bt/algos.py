from bt.core import Algo
import pandas as pd


class DatePrintAlgo(Algo):

    def __call__(self, target):
        print target.now
        return True


class RunOnce(Algo):

    """
    Returns True on first run then returns False

    As the name says, the algo only runs once. Useful in situations
    where we want to run the logic once (buy and hold for example).
    """

    def __init__(self):
        super(RunOnce, self).__init__()
        self.has_run = False

    def __call__(self, target):
        # if it hasn't run then we will
        # run it and set flag
        if not self.has_run:
            self.has_run = True
            return True

        # return false to stop future execution
        return False


class RunWeekly(Algo):

    """
    Returns True on week change.

    Returns True if the target.now's week has changed
    since the last run, if not returns False. Useful for
    weekly rebalancing strategies.
    """

    def __init__(self):
        super(RunWeekly, self).__init__()
        self.last_date = None

    def __call__(self, target):
        # get last date
        now = target.now

        # if none nothing to do - return false
        if now is None:
            return False

        # create pandas.Timestamp for useful .week property
        now = pd.Timestamp(now)

        if self.last_date is None:
            self.last_date = now
            return False

        result = False
        if now.week != self.last_date.week:
            result = True

        self.last_date = now
        return result


class RunMonthly(Algo):

    """
    Returns True on month change.

    Returns True if the target.now's month has changed
    since the last run, if not returns False. Useful for
    monthly rebalancing strategies.
    """

    def __init__(self):
        super(RunMonthly, self).__init__()
        self.last_date = None

    def __call__(self, target):
        # get last date
        now = target.now

        # if none nothing to do - return false
        if now is None:
            return False

        if self.last_date is None:
            self.last_date = now
            return False

        result = False
        if now.month != self.last_date.month:
            result = True

        self.last_date = now
        return result


class RunYearly(Algo):

    """
    Returns True on year change.

    Returns True if the target.now's year has changed
    since the last run, if not returns False. Useful for
    yearly rebalancing strategies.
    """

    def __init__(self):
        super(RunYearly, self).__init__()
        self.last_date = None

    def __call__(self, target):
        # get last date
        now = target.now

        # if none nothing to do - return false
        if now is None:
            return False

        if self.last_date is None:
            self.last_date = now
            return False

        result = False
        if now.year != self.last_date.year:
            result = True

        self.last_date = now
        return result


class RunOnDate(Algo):

    """
    Returns True on a specific set of dates.
    """

    def __init__(self, *dates):
        """
        Args:
            * dates (*args): A list of dates. Dates will be parsed
                by pandas.to_datetime so pass anything that it can
                parse. Typically, you will pass a string 'yyyy-mm-dd'.
        """
        super(RunOnDate, self).__init__()
        # parse dates and save
        self.dates = [pd.to_datetime(d) for d in dates]

    def __call__(self, target):
        return target.now in self.dates


class SelectAll(Algo):

    def __init__(self):
        super(SelectAll, self).__init__()

    def __call__(self, target):
        target.algo_data['selected'] = target.universe.columns
        return True


class WeighEqually(Algo):

    def __init__(self):
        super(WeighEqually, self).__init__()

    def __call__(self, target):
        selected = target.algo_data['selected']
        n = len(selected)

        if n == 0:
            target.algo_data['weights'] = {}
        else:
            w = 1.0 / n
            target.algo_data['weights'] = {x: w for x in selected}

        return True


class CapitalFlow(Algo):

    """
    Used to model capital flows. Flows can either be inflows or outflows.

    This Algo can be used to model capital flows. For example, a pension
    fund might have inflows every month or year due to contributions. This
    Algo will affect the capital of the target node without affecting returns
    for the node.
    """

    def __init__(self, amount):
        """
        CapitalFlow constructor.

        Args:
            * amount (float): Amount to adjust by
        """
        super(CapitalFlow, self).__init__()
        self.amount = float(amount)

    def __call__(self, target):
        target.adjust(self.amount)
        return True


class Rebalance(Algo):

    """
    Rebalances capital based on algo_data weights.

    Rebalances capital based on algo_data['weighs']. Also closes
    positions if open but not in target_weights. This is typically
    the last Algo called once the target weights have been set.
    """

    def __init__(self):
        super(Rebalance, self).__init__()

    def __call__(self, target):
        targets = target.algo_data['weights']

        # de-allocate children that are not in targets
        not_in = [x for x in target.children if x not in targets]
        for c in not_in:
            target.close(c)

        # save value because it will change after each call to allocate
        # use it as base in rebalance calls
        base = target.value
        for item in targets.iteritems():
            target.rebalance(item[1], child=item[0], base=base)

        return True
