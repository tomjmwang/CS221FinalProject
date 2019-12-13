# CS221FinalProject

Code for Fall 2019 CS221 final project, An Intelligent Coup Agent.

Three code files: game.py, qlearning.py, featureqlearning.py. Each can be run directly with Python 3.

**game.py** is a simulator of Coup. Running the following command

<code>python3 game.py</code>

runs the game simulator 1000 times and outputs counts of wins of each player.

**qlearning.py** implements vanilla Q-Learning algorithm on the Coup simulator. Running the following command

<code>python3 qlearning.py</code>

runs 3000000 iterations to train the first agent using default setting (3 players, 3000000 iterations, 30 break points). Policy will be calculated at 
each break point and evaluated for 10000 trials.

**featureqlearning.py** implements Q-Learning using our engineered feature state approximation to learn optimal policy. To run the file, execute the following command:

<code>python3 featureqlearning.py</code>

It runs the experiment under default setting.

The default settings for qlearning.py and featureqlearning.py can be adjusted by changing the variables at the start of main() functions of each file.
