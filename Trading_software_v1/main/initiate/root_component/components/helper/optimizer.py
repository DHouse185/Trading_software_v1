##########  Python IMPORTs  ############################################################
import typing
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################

########################################################################################
##########  Created files IMPORTS  #####################################################
from initiate.root_component.strategies.optimizing import Nsga2
########################################################################################


def run(backtest_widget, parameters: typing.Dict):
    """
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
            "Generation_Size"  : self.body_widgets['Generation_Size'][2].text()
            "Extra_Parameters" : self._extra_input
            }   
    """
    # Population Size        
    pop_size = int(parameters["Population_Size"]) 
 
    # Iterations
    generations = int(parameters["Generation_Size"]) 
        
    nsga2 = Nsga2(backtest_widget, parameters, pop_size)

    p_population = nsga2.create_initial_population()
    p_population = nsga2.evaluate_population(p_population)
    p_population = nsga2.crowding_distance(p_population)

    g = 0

    while g < generations:
        
        q_population = nsga2.create_offspring_population(p_population)
        q_population = nsga2.evaluate_population(q_population)
        
        r_population = p_population + q_population
        
        nsga2.population_params.clear()

        i = 0 
        population = dict()
        
        for bt in r_population:
            bt.reset_results()
            nsga2.population_params.append(bt.parameters)
            population[i] = bt
            i += 1
        
        fronts = nsga2.non_dominated_sorting(population)
        for j in range(len(fronts)):
            fronts[j] = nsga2.crowding_distance(fronts[j])
        
        p_population = nsga2.create_new_population(fronts)
        
        backtest_widget._add_log(f"\r{int((g + 1) / generations * 100)}%")
        
        g += 1
        
    backtest_widget._add_log("\n")
        
    for individual in p_population:
        backtest_widget._add_log(f"{individual}")