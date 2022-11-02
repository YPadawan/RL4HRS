import pandas as pd

price_dict = {"P": 7.154,
              "HPH": 5.820,
              "HCH": 4.452,
              "HCE": 2.820}


def grid_tariffs(date):
    month = date.month
    hour = date.hour

    if month in [1, 2, 12]:

        if (hour >= 6 and hour < 8) or \
                (hour >= 10 and hour < 17) or \
                (hour >= 19 and hour < 22):

            x = 'HPH'

        elif (hour >= 8 and hour < 10) or \
                (hour >= 17 and hour <= 19):

            x = 'P'

        else:
            x = 'HCH'

    elif month in [3, 11]:

        if hour >= 6 and hour < 22:
            x = 'HPH'
        else:
            x = 'HCH'
    else:
        if hour >= 6 and hour < 22:
            x = 'HPE'
        else:
            x = 'HCE'

    return x