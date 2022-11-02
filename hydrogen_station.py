class WindTurbine:

    def __init__(self, cut_in_speed=3.5, cut_out_speed=20,
                 rated_speed=10, rated_power=100):

        self.cut_in_speed = cut_in_speed
        self.cut_out_speed = cut_out_speed
        self.rated_speed = rated_speed
        self.rated_power = rated_power
        # self.power = power

    def power_generation(self, speed):

        if speed <= self.cut_in_speed or speed >= self.cut_out_speed:

            power = 0.  # put the formula here

        elif speed >= self.cut_in_speed and speed < self.rated_speed:

            denominator = self.rated_speed - self.cut_in_speed

            power = speed * (self.rated_power / denominator)
            power -= self.rated_power * (self.cut_in_speed / denominator)
            # write at the end annoying

        elif speed >= self.rated_speed and speed < self.cut_out_speed:

            power = self.rated_power
        else:
            raise ValueError('There is a problem')

        return power


class Electrolyser:

    def __init__(self, lhv=33.3, efficiency=0.6,
                 min_power=0, max_power=600, hour_prod=10):
        self._lhv = lhv  # in kWh/kg
        self._efficiency = efficiency  # 60%
        self._min_power = min_power  # kW
        self._max_power = max_power  # kW
        self._hour_prod = hour_prod  # hydrogen produced per hour in kg

    def power_consumption(self, delta=1):
        power_need = (self._hour_prod * self._lhv / self._efficiency * delta)
        return power_need * 100

    def get_hour_prod(self):
        """returns the amount of hydrogen produced per hour. It is an attribute defined outside"""
        return self._hour_prod


class Compressor:

    def __init__(self, heat_cp=14.304,
                 pressure_in=1, pressure_out=90,
                 t_in=293, motor_eff=0.9,
                 comp_eff=0.7, r=1.4):
        # Specific heat of hydrogen at constant pressure [kJ/kg/K]
        self.heat_cp = heat_cp
        self.pressure_in = pressure_in  # MPa
        self.pressure_out = pressure_out  # MPa
        self.t_in = t_in  # Hydrogen temperature at the compressor inlet [K]
        self.motor_eff = motor_eff  # %
        self.comp_eff = comp_eff  # %
        self.r = r  # ratio of specific heat of hydrogen

    def power_consumption(self, h_prod, delta=1):
        power = self.heat_cp * ((self.t_in * 1e4) / self.motor_eff * self.comp_eff * delta)
        power = power * ((self.pressure_out / self.pressure_in) ** ((self.r - 1) / self.r) - 1)
        power = power * (h_prod / 3600)

        return power


class StorageTanks:

    def __init__(self, min_capacity=3,
                 max_capacity=30,
                 loss_coef=0.01):
        self.min_capacity = min_capacity  # kg
        self.max_capacity = max_capacity  # kg
        self.loss_coef = loss_coef  # %
        self.capacity = max_capacity / 2  # should perhaps be made into a private attribute ._capacity

    def available_amount(self, step_idx, h_prod_elec, h_demand):
        storage_amount = (1 - self.loss_coef) * self.capacity

        storage_amount = storage_amount + h_prod_elec - h_demand

        self.capacity = storage_amount

    def get_capacity(self):
        return self.capacity

    def set_capacity(self, capacity):
        self.capacity = capacity

    def store_hydrogen(self, hy_amount):
        self.capacity += hy_amount


class PreCooling:

    def __init__(self, chill_energy=0.33):
        self.chill_energy = chill_energy

    def power_consumption(self, h_demand):
        return self.chill_energy * h_demand


class HydrogenStation:

    def __init__(self, wind_turbine):
        """Class for the hydrogen station, using all different components of the station,
        the electrolyser, the compressor, the storage tank, the pre cooling unit in addition
        to the renewable energy components"""

        self.electrolyser = Electrolyser()
        self.compressor = Compressor()
        self.storage_tank = StorageTanks()
        self.pre_cooling = PreCooling()
        self.wind_turbine = wind_turbine

    def power_consumption(self, hy_demand, wind_speed, delta_elec=1, delta_comp=1):

        hy_prod = self.electrolyser.get_hour_prod()  # get the hour production of the electrolyser

        pc_elec = self.electrolyser.power_consumption(delta_elec)
        pc_comp = self.compressor.power_consumption(delta_comp, hy_prod)  # hourly production
        pc_precool = self.pre_cooling.power_consumption(hy_demand)

        # Compute the amount of power necessary for the station's components
        station_power = pc_elec + pc_comp + pc_precool

        # Get the clean power production
        clean_power = self._clean_energy_production(wind_speed)

        # Compute total needed power
        required_power = station_power - clean_power

        if required_power <= 0.:
            # If required power is null or negative, it means that all electricity consumption
            # is covered the renewable energy source that makes free electricity
            return 0.

        else:

            return required_power

    def buy_from_grid(self, hy_demand, price, wind_speed, delta_elec=1, delta_comp=1):

        required_power = self.power_consumption(hy_demand, wind_speed,
                                                delta_elec, delta_comp)
        elec_price = required_power * price

        return elec_price

    def _clean_energy_production(self, wind_speed):

        clean_power = self.wind_turbine.power_generation(wind_speed)
        return clean_power

    def refuel(self, hy_demand, wind_speed, price):

        capacity = self.storage_tank.get_capacity()

        if hy_demand <= capacity:

            capacity -= hy_demand
            self.storage_tank.set_capacity(capacity)  # Updates the storage capacity

        else:  # Hydrogen needs to be produced
            required_power = self.power_consumption(hy_demand, wind_speed)
            elec_price = self.buy_from_grid(required_power, price)

            # Because it is fixed to 10 kg per hour, hourly production of electrolyser
            self.storage_tank.set_capacity(10)
            capacity = self.storage_tank.get_capacity()
            new_capacity = capacity - hy_demand
            self.storage_tank.set_capacity(new_capacity)

    def store_hydrogen(self):
        pass
