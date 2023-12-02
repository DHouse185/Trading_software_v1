##########  Python IMPORTs  ############################################################
import random
import typing
import copy
########################################################################################
##########  Created files IMPORTS  #####################################################
from initiate.root_component.components.helper.hdfs_database import Hdf5Client
import initiate.root_component.util.root_variables as r_var
from initiate.root_component.strategies.backtesting import (TechnicalStrategy, 
                                                           BreakoutStrategy)
from initiate.connectors.models import Backtestresults
########################################################################################

class Nsga2:
    """
    ---------------
    used for backtest_widget._add_log:
    This is so information can be sent to the ui.\n
    Example : backtest_widget._add_log(str(message))\n
    Example
    ---------
    Here strategies have their own function in the form 
    of a dictionary.\n
    Example
    ---------
    strategies = {Technical: strategy.technical.backtest,
    Breakout: strategy.breakout.backtest,
    Ichimoku: strategy.breakout.backtest
    MACD_and_Breakout: strategy.macd_and_breakout.backtest}\n
    You will also pass the strategy function a dictionary of the
    parameters needed for backtesting\n
    Example
    ----------
    strategy.technical.backtest(data: pd.DataFrame, parameter: List[Dict])
    where parameters:
    parameters = [{
        "Balance": 2500,
        "Balance_percent" : 0.02,
        "Take_Profit": 0.02,
        "Stop_Loss": 0.005
        },
                  # Extra Parameters
                  {"rsi_signal": 30,
                   "macd_signal": 50,
                   "macd_fast": 12,
                   "macd_slow": 25,
                   "volume": 400}]
     or
     parameters = {
            "Strategy"         : self.initialize_strategy.currentText(),
            "Pair"             : symbol,
            "Exchange"         : symbol_exchange,
            "Client"           : self._exchanges[symbol_exchange],
            "TimeFrame"        : self.body_widgets['timeframe'][2].currentText(),
            "Balance_percent"  : self.body_widgets['balance_percentage'][2].text(),
            "Take_Profit"      : self.body_widgets['take_profit'][2].text(),
            "Stop_Loss"        : self.body_widgets['stop_loss'][2].text(),
            "From_Time"        : (self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "To_Time"          : (self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "Population_Size"  : self.body_widgets['Population_Size'][2].text()
            "Extra_Parameters" : self._extra_input
            }   
    - Make dictionary of strategy types with their function
    strategy_types = {"Technical": technical.backtest,
                       "Breakout": breakout.backtest}
    - Don't forget to update this with r_var.STRTEGIES
    - Go into data history and retrieve data
    h5_db = Hdf5Client(exchange, backtest_widget)

    - from_time and to_time are QDateTime objects, so they need to be converted to 
    - from_time.toSecsSinceEpoch() * 1000 and 
    - to_time.toSecsSinceEpoch() * 1000
    """
    def __init__(self, backtest_widget, parameters: typing.Dict, population_size):
        # Make dictionary of strategy types with their function
    # Don't forget to update this with r_var.STRTEGIES
        self.parameters = parameters
        self.strategies_backtest = {"Technical": True,
                            "Breakout": BreakoutStrategy,
                            "Test_Strat": True}
        self.exchange = parameters["Exchange"]
        self.symbol = parameters["Pair"] 
        self.strategy = parameters["Strategy"] 
        self.timeframe = parameters["TimeFrame"] 
        self.from_time = parameters["From_Time"] 
        self.to_time = parameters["To_Time"] 
        self.population_size = population_size 
        
        self.params_data = r_var.EXTRA_PARAMETERS[self.strategy]
        
        self.population_params = []
        
        h5_db = Hdf5Client(self.exchange, backtest_widget=backtest_widget)
        self.data = h5_db.get_data(symbol=self.symbol, from_time=self.from_time, to_time=self.to_time)
        self.data = r_var.resample_timeframe(self.data, self.timeframe)
                
    def create_initial_population(self) -> typing.List[Backtestresults]:
        population = []
        
        while len(population) < self.population_size:
            
            backtest = Backtestresults()

            for strategy_param in self.params_data:
                
                for p_code, p in strategy_param.items():
                    
                    if p["data_type"] == int:
                        backtest.parameters[strategy_param["code_name"]] = random.randint(p["min"], p["max"])
                        
                    elif p["data_type"] == float:
                        backtest.parameters[strategy_param["code_name"]] = round(random.uniform(p["min"], p["max"]), p["decimals"])
                
            if backtest not in population:
                population.append(backtest)
                self.population_params.append(backtest.parameters)
                 
        return population
    
    def create_new_population(self, fronts: typing.List[typing.List[Backtestresults]]) -> typing.List[Backtestresults]:
        
        new_pop = []
        
        for front in fronts:
            
            if len(new_pop) + len(front) > self.population_size:
                max_individuals = self.population_size - len(new_pop)
                
                if max_individuals > 0:
                    new_pop += sorted(front, key=lambda x: getattr(x, "crowding_distance"))[-max_individuals:]
                
            else:
                new_pop += front

        return new_pop
      
    def _params_constraints(self, params: typing.Dict) -> typing.Dict:
        if self.strategy == "Breakout":
            pass
        elif self.strategy == "Technical":
            # params["kijun"] = max(params["kijun"], params["tenkan"])
            pass
        ...
        
        # if self.strategy == "obv":
        #     pass
        # elif self.strategy == "sup_res":
        #     pass
        # elif self.strategy == "ichimoku":
        #     params["kijun"] = max(params["kijun"], params["tenkan"])
        # elif self.strategy == "sma":
        #     params["slow_ma"] = max(params["slow_ma"], params["fast_ma"])
        # elif self.strategy == "psar":
        #     params["initil_acc"] = min(params["initial_acc"], params["max_acc"])
        #     params["acc_increment"] = min(params["acc_increment"], params["max_acc"] - params["initial_acc"])
            
        return params
       
    def crowding_distance(self, population: typing.List[Backtestresults]) -> typing.List[Backtestresults]:
        for objective in ["pnl", "max_dd"]:
            
            population = sorted(population, key=lambda x: getattr(x, objective))
            min_value = getattr(min(population, key=lambda x: getattr(x, objective)), objective)
            max_value = getattr(max(population, key=lambda x: getattr(x, objective)), objective)
            
            population[0].crowding_distance = float("inf")
            population[-1].crowding_distance = float("inf")
            
            for i in range(1, len(population) - 1):
                
                distance = getattr(population[i + 1], objective) - getattr(population[i - 1], objective)
                
                if max_value - min_value != 0:
                    distance = distance / (max_value - min_value)
                    
                population[i].crowding_distance += distance
                
        return population
    
    def create_offspring_population(self, population: typing.List[Backtestresults]) -> typing.List[Backtestresults]:
        ...
        offspring_pop = []
        
        while len(offspring_pop) != self.population_size:
            
            parents: typing.List[Backtestresults] = []
            
            for i in range(2):
                
                random_parents = random.sample(population, k=2)
                
                if random_parents[0].rank != random_parents[1].rank:
                    best_parent = min(random_parents, key=lambda x: getattr(x, "rank"))
                    
                else:
                    best_parent = max(random_parents, key=lambda x: getattr(x, "crowding_distance"))
                    
                parents.append(best_parent)
                
            new_child = Backtestresults()
            new_child.parameters = copy.copy(parents[0].parameters)
            
            # Crossover
            
            number_of_crossovers = random.randint(1, len(self.params_data))
            params_to_cross = random.sample(([strategy_param["code_name"] for strategy_param in self.params_data]), k=number_of_crossovers)
            
            for p in params_to_cross:
                new_child.parameters[p] = copy.copy(parents[1].parameters[p])
                
            # Mutation
            
            number_of_mutations = random.randint(0, len(self.params_data))
            params_to_change = random.sample(([strategy_param["code_name"] for strategy_param in self.params_data]), k=number_of_mutations)
            
            for p in params_to_change:
                
                for stratg in self.params_data:
                    
                    if stratg["code_name"] == p:
                        mutations_strength = random.uniform(-2, 2)
                        new_child.parameters[p] = stratg["data_type"](new_child.parameters[p] * (1 + mutations_strength))
                        new_child.parameters[p] = max(new_child.parameters[p], stratg["min"])
                        new_child.parameters[p] = min(new_child.parameters[p], stratg["max"])
                
                        if stratg["data_type"] == float:
                            new_child.parameters[p] = round(new_child.parameters[p], stratg["decimals"])
                    
            new_child.parameters = self._params_constraints(new_child.parameters)
                    
            if new_child.parameters not in self.population_params:
                offspring_pop.append(new_child)
                self.population_params.append(new_child.parameters)
                
        return offspring_pop
            
    def non_dominated_sorting(self, population: typing.Dict[int, Backtestresults]) -> typing.List[typing.List[Backtestresults]]:
        fronts = [] 
        
        for id_1, indiv_1 in population.items():
            
            for id_2, indiv_2 in population.items():
                
                if indiv_1.pnl >= indiv_2.pnl and indiv_1.max_dd <= indiv_2.max_dd \
                and (indiv_1.pnl > indiv_2.pnl or indiv_1.max_dd < indiv_2.max_dd):
                    indiv_1.dominates.append(id_2 )
                        
                elif indiv_2.pnl >= indiv_1.pnl and indiv_2.max_dd <= indiv_1.max_dd \
                and (indiv_2.pnl > indiv_1.pnl or indiv_2.max_dd < indiv_1.max_dd):
                    indiv_1.dominated_by += 1
                        
            if indiv_1.dominated_by == 0:
                
                if len(fronts) == 0:
                    fronts.append([])
                    
                fronts[0].append(indiv_1)
                indiv_1.rank = 0
                
        i = 0
        
        while True:        
            fronts.append([])
            
            for indiv_1 in fronts[i]:
                
                for indiv_2_id in indiv_1.dominates:
                    population[indiv_2_id].dominated_by -= 1
                    
                    if population[indiv_2_id].dominated_by == 0:
                        fronts[i + 1].append(population[indiv_2_id])
                        population[indiv_2_id].rank = i + 1
                        
            if len(fronts[i + 1]) > 0:
                i += 1
                
            else:
                del fronts[-1]
                break
            
        return fronts
    
    def evaluate_population(self, population: typing.List[Backtestresults]) -> typing.List[Backtestresults]:
        for bt in population:
            strategy = self.strategies_backtest[self.strategy](data=self.data, parameters=self.parameters)        
            bt.pnl, bt.max_dd, df_results = strategy.run()
            
            if bt.pnl == 0:
                bt.pnl = -float("inf")
                bt.max_dd = float("inf")
                
        return population
        