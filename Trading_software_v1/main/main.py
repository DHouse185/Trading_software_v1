# This is the start of the trading platform.
# You should be able to manage your portfolio across
# different trading platforms, trade on these platform,
# create strategies for bots, backtest strategies, and
# optimze them. Good Luck! 
# Please do not edit this file

##########  Created files IMPORTS  #####################################################
import logger
from initiate.login_handler import Login
########################################################################################

# Set up logger
log = logger.main()
# Begin application from here
if __name__ == "__main__":
    main_start = Login(log)
    