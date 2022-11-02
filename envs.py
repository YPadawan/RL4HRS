import gym
import numpy as np
from gym import spaces
from hydrogen_station import WindTurbine, HydrogenStation


class HydrogenStationEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, df):
        super(HydrogenStationEnv, self).__init__()

        # Defining all the components of the

        #         self.episode_idx = 0
        self.current_step = 0
        self.df = df  # takes the dataframe containing the required information
        self.storage_capacity = 30

        wt = WindTurbine()  # Energy produced by wind turbine will always be used when possible

        self.hrs = HydrogenStation(wt)

        # Three basic actions are defined:
        # - Buy electricity from the grid to produce hydrogen and store it
        # - Store hydrogen produced from renewable energy
        # - Do nothing
        self.action_space = spaces.Discrete(3)

        # The observation space is a basic numpy array containing the following information:
        # - The wind speed at hour h (m.s-1)
        # - The fcev demand at hour h (number of vehicles to fuel)
        # - The h2 amount needed (in kg of hydrogen)
        # - The month
        # - The hour
        # - The price of electricity at hour h (based on the hour and month for the season)
        # - Th storage amount of hydrogen available (for the moment, the only information that the agent modifies)
        # For the moment, only one row for with the data at hour h is used
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(7,), dtype=np.float64)

    def reset(self):

        # Reset the env

        self.storage_capacity = 30

        # Set the current step to a random point within the data frame's length
        # self.current_step = random.randint(0, len(self.df)-26)
        self.current_step = 0

        frame = self.df.iloc[self.current_step].values
        obs = np.append(frame, [self.storage_capacity], axis=0)

        return obs

    def step(self, action: any) -> 'Tuple[np.array, float, bool, dict]':

        price = self.df.iloc[self.current_step]['prices']
        hy_demand = self.df.iloc[self.current_step]['h2_amount']
        wind_speed = self.df.iloc[self.current_step]['wind_speed']

        # initializing a reward
        reward = 0.

        # Hydrogen demand must be always be satisfied
        remnant = self.storage_capacity - hy_demand
        if remnant <= 0:
            while remnant <= 0:
                elec_price = self.hrs.buy_from_grid(hy_demand, price, wind_speed)
                reward += -1 * elec_price
                self.storage_capacity += self.hrs.electrolyser.get_hour_prod()  # adding the hour production
                remnant = self.storage_capacity - hy_demand

            self.storage_capacity -= hy_demand
        else:
            self.storage_capacity -= hy_demand

        if action == 0:

            # Buy power and store hydrogen
            # For this we need the hour for grid prices

            # Then we will need to buy power for hydrogen production
            elec_price = self.hrs.buy_from_grid(10., price, wind_speed, clean=False)
            reward += -1 * elec_price

            # Once electricy is bought, hydrogen has to be stored -> need to increase storage capacity

            self.storage_capacity += self.hrs.electrolyser.get_hour_prod()  # adding the hour production


        elif action == 1:

            # elec_price = self.hrs.buy_from_grid(5., price, wind_speed)
            renewable_power = wt.power_generation(wind_speed)
            pc_hy_10 = self.hrs.power_consumption(10, wind_speed, clean=False)
            ratio = renewable_power / pc_hy_10
            hy_amount = 10 * ratio
            reward += price * renewable_power

            # Storing a renewable energy hydrogen with 0 cost, for the moment fixed at 5 kg
            self.storage_capacity += hy_amount

        elif action == 2:
            # do nothing, no reward, no storage
            reward += 0.

        else:
            raise ValueError(
                "Received invalid action={} which is not in the action space".format(action))

        frame = self.df.iloc[self.current_step, :].values
        observation = np.append(frame, [self.storage_capacity])

        self.current_step += 1
        done = (self.current_step == len(self.df) - 1)  # Is done when all the dataframe has been iterated
        info = {}  # to fill later

        return observation, reward, done, info

    def render(self, mode='human'):

        hy_demand = self.df.iloc[self.current_step]['h2_amount']
        print(f"action taken: {action}")
        print(f"hydrogen demand is: {hy_demand}")
        print(f"current storage capacity is : {self.storage_capacity}")
        print(f"current step: {self.current_step}")
        print("----------current values-------------")
        print(self.df.iloc[self.current_step].values)

    def close(self):
        pass