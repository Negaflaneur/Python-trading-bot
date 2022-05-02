# Binance spot trading bot

A binance trading bot for spot trading using Binance API that uses MACD and PSAR technical indicators to analyse the market.

## Description

The project is a cryptocurrency trading bot written in Python, intended to require minimal user intervention.
It is observed that the market price can be analysed using several technical indicators to enter and close the trades at the maximum profit

It operates on the spot market by listening to the price data stream and identifying trade opportunites based on the market trend and recent behaviour.

Moving Average Convergence Divergence(MACD) is a technical indicator that measures the relationship between 12 and 26 period moving averages to generate trade signals.
MACD is used as a crossover indicator and oscillator indicator.

Parabolic SAR is a trend reversal indicator which is used for identifying changes in the trend direction. 
Combined with the MACD indicator, it filters out the market noise to close trades at maximum profit

The strategy is integrated -- the bot only needs a predefined configuration to run.

## Getting Started

### RISK ALERT
⚠️ Use at own risk ⚠️

### Dependencies

* Python
* Binance API
* Pandas 
* Numpy
* Btalib
* Requests

### Set-up 

* Create a Binance account
* Enable Two-factor Authentication.
* Create a new pair of API keys.

### Executing program

* Connect the script to your account using the API KEYS.
* Run and install necessary dependencies 
* Choose or modify the pair you want to trade
* Run the script and enjoy automated trading: 
*     python -m bin.py

## Reducing fees

You can use BNB to pay for any fees on the Binance platform, which will reduce all fees by 25%. In order to support this benefit, the bot will always perform the following operations:

* Automatically detect that you have BNB fee payment enabled.
* Make sure that you have enough BNB in your account to pay the fee of the inspected trade.
* Take into consideration the discount when calculating the trade threshold.

## Authors

Negaflaneur

## Contributions
To make sure your code is properly formatted before making a pull request, remember to install pre-commit:

    pip install pre-commit
    pre-commit install
The scouting algorithm is unlikely to be changed. If you'd like to contribute an alternative method, add a new strategy.

## Version History

* 0.1
    * Initial Release

## License
Released freely without conditions. Anybody may copy, distribute, modify, use or misuse for commercial, non-commercial, educational or non-educational purposes, censor, claim as one's own or otherwise do whatever without permission from anybody.
