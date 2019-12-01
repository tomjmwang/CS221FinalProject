import game
import collections
import random
import pickle
import time

class QLearning(game.Game):

    def __init__(self, cards, player_card_num=2, num_players=3):
        self.num_players = num_players
        self.starting_player = 0
        self.last_player = 0
        self.game_state = None  # ((player 1's cards, player 2's cards, player 3's cards), (each player's coins), current action/counteraction, effective)
        self.cards = cards
        self.player_card_num = player_card_num
        self.card_functions = {"assassin": ["assassinate"], "duke": ["tax", "block_foreign_aid"], "captain": ["steal", "block_steal"], "ambassador": ["exchange", "block_steal"], "contessa": ["block_assassinate"]}        
        self.function_to_char = {}
        for k,v in self.card_functions.items():
            for n in v:
                self.function_to_char[n] = k
        self.player_state = None
        self.Q = collections.defaultdict(float)
        self.eps = 0.2
        self.discount = 0.95
        self.alpha = 0.05
        self.pi = {}
        self.e = 0
        self.f = 0
        self.last_state = None
        self.accum_reward = 0

    def isEndState(self, state):
        dead_players = 0
        for player_cards in state[0]:
            all_inactive = True
            for card in player_cards:
                if card[1] != 2:
                    all_inactive = False
                    break
            if all_inactive:
                dead_players += 1
        if dead_players == self.num_players - 1:
            return True
        return False

    def convertGameState(self):
        element1 = [self.game_state[0][0]]
        for player_cards in self.game_state[0][1:]:
            temp_cards = []
            living_cards = 0
            for card in player_cards:
                if card[1] == 1:
                    temp_cards.append(("unknown",1))
                    living_cards += 1
                else:
                    temp_cards.append(card)
            #element1.append(tuple(temp_cards))
            element1.append(living_cards)
        element1 = tuple(element1)
        self.player_state = (element1, self.game_state[1], self.game_state[2],self.game_state[3])

    def reward(self, old_state, action, new_state):
        score = 0.0
        if self.isEndState(new_state) and self.getNextLivingPlayer(0) == 0:
            score += 1000.0

        num_living_old = 0
        num_living_new = 0
        for j, card in enumerate(old_state[0][0]):
            if card[1] == 1:
                num_living_old += 1
            if new_state[0][0][j][1] == 1:
                num_living_new += 1

        score -= 500 * (num_living_old - num_living_new)

        for i in range(1, self.num_players):
            num_living_old = 0
            num_living_new = 0
            for j, card in enumerate(old_state[0][i]):
                if card[1] == 1:
                    num_living_old += 1
                if new_state[0][i][j][1] == 1:
                    num_living_new += 1
            score += (num_living_old - num_living_new) * 100



        return score

    def chooseQAction(self, actions, state):
        if random.random() < self.eps:
            chosen_action = random.choice(actions)
            return chosen_action, self.Q[(state,chosen_action)]
        max_q = float('-inf')
        max_action = None
        for action in actions:
            if self.Q[(state,action)] > max_q:
                max_q = self.Q[(state,action)]
                max_action = action
        return max_action, max_q

    def calculatePolicy(self):
        self.pi = {}
        state_to_q = {}
        for k,v in self.Q.items():
            if k[0] not in state_to_q:
                self.pi[k[0]] = k[1]
                state_to_q[k[0]] = v
            else:
                if v > state_to_q[k[0]]:
                    state_to_q[k[0]] = v
                    self.pi[k[0]] = k[1]
        print(len(self.pi))


    def simulateQLearning(self):
        player_cards = []
        for i in range(self.num_players):
            each_player_cards = []
            for j in range(self.player_card_num):
                card = self.cards.pop(0)
                add_card = (card[0], 1)
                each_player_cards.append(add_card)
            player_cards.append(tuple(each_player_cards))
        self.game_state = (tuple(player_cards), tuple([2 for i in range(self.num_players)]), None, False)
        #print("initial state: ", self.game_state)
        current_player = self.starting_player
        while True:
            actions = self.getActions(current_player, self.game_state)
            if len(actions) == 0:
                cur_action = self.game_state[2]
                if not self.game_state[3]:
                    if cur_action[0] == "tax" or cur_action[0] == "foreign_aid":
                        new_player = self.getNextLivingPlayer(self.game_state[2][1])
                        new_state = self.takeEffect(self.game_state, self.game_state[2])
                    elif len(cur_action[0]) > 5 and cur_action[0][:5] == "block":
                        new_player = self.getNextLivingPlayer(self.game_state[2][2])
                        new_state = (self.game_state[0], self.game_state[1], None, False)
                        #print("Player", cur_action[1], "blocked player", cur_action[2])
                    else:
                        new_player = cur_action[2]
                        new_state = (self.game_state[0], self.game_state[1], cur_action, True)
                else:
                    new_state = self.takeEffect(self.game_state, self.game_state[2])
                    new_player = self.getNextLivingPlayer(self.game_state[2][1])
            else:
                if current_player == 0:
                    #action = self.chooseBaseLineAction(actions, self.game_state)
                    self.convertGameState()
                    action, max_q = self.chooseQAction(actions,self.player_state)

                else:
                    #action = self.chooseRandomAction(actions)
                    action = self.chooseBaseLineAction(actions, self.game_state)
                new_state, new_player = self.succ(action, self.game_state)
            if current_player == 0 and len(actions) > 0:
                if self.last_state:
                    last_state = self.last_state
                    cur_state = self.game_state
                    last_action = self.last_action
                    last_q = self.Q[(last_state,last_action)] 
                    r = self.accum_reward
                    self.Q[(last_state,last_action)] = last_q + self.alpha*(r + self.discount*max_q - last_q)
                    self.accum_reward = 0
                self.last_state = self.player_state
                self.last_action = action
            self.accum_reward += self.reward(self.game_state, action, new_state)
            self.game_state = new_state
            current_player = new_player
            if self.isDead(current_player):
                current_player = self.getNextLivingPlayer(current_player)
            #print("Current state: ", self.game_state)
            if self.isEnd():
                winner = self.getNextLivingPlayer(current_player)
                last_q = self.Q[(last_state,last_action)]
                if winner == 0:
                    r = self.accum_reward
                    self.Q[(last_state,last_action)] = last_q + self.alpha*(r - last_q)
                else:
                    r = -1000
                    self.Q[(last_state,last_action)] = last_q + self.alpha*(r - last_q)
                self.accum_reward = 0
                #print("Player", winner, "wins!")
                break
        return winner

    def evaluatePolicy(self, policy):
        player_cards = []
        for i in range(self.num_players):
            each_player_cards = []
            for j in range(self.player_card_num):
                card = self.cards.pop(0)
                add_card = (card[0], 1)
                each_player_cards.append(add_card)
            player_cards.append(tuple(each_player_cards))
        self.game_state = (tuple(player_cards), tuple([2 for i in range(self.num_players)]), None, False)
        #print("initial state: ", self.game_state)
        current_player = self.starting_player
        while True:
            actions = self.getActions(current_player, self.game_state)
            if len(actions) == 0:
                cur_action = self.game_state[2]
                if not self.game_state[3]:
                    if cur_action[0] == "tax" or cur_action[0] == "foreign_aid":
                        new_player = self.getNextLivingPlayer(self.game_state[2][1])
                        new_state = self.takeEffect(self.game_state, self.game_state[2])
                    elif len(cur_action[0]) > 5 and cur_action[0][:5] == "block":
                        new_player = self.getNextLivingPlayer(self.game_state[2][2])
                        new_state = (self.game_state[0], self.game_state[1], None, False)
                        #print("Player", cur_action[1], "blocked player", cur_action[2])
                    else:
                        new_player = cur_action[2]
                        new_state = (self.game_state[0], self.game_state[1], cur_action, True)
                else:
                    new_state = self.takeEffect(self.game_state, self.game_state[2])
                    new_player = self.getNextLivingPlayer(self.game_state[2][1])
            else:
                if current_player == 0:
                    #action = self.chooseBaseLineAction(actions, self.game_state)
                    self.convertGameState()
                    try:
                        action = policy[self.player_state]
                        #print("Current state:", self.game_state)
                        #print("Chosen action:", action)
                        if action not in actions:
                            action = self.chooseRandomAction(actions)
                        self.f += 1
                    except:
                        self.e += 1
                        action = self.chooseRandomAction(actions)
                        #print("errorfound")
                else:
                    #action = self.chooseRandomAction(actions)
                    action = self.chooseBaseLineAction(actions, self.game_state)
                new_state, new_player = self.succ(action, self.game_state)
            self.game_state = new_state
            current_player = new_player
            if self.isDead(current_player):
                current_player = self.getNextLivingPlayer(current_player)
            if self.isEnd():
                winner = self.getNextLivingPlayer(current_player)
                break
        return winner

def main():
    cards = [("duke",1), ("duke",1),("assassin",1),("assassin",1),("contessa",1),("contessa",1),("captain",1),("captain",1),("ambassador",1),("ambassador",1)]
    rl = QLearning(cards, num_players=3)
    
    output_file = open("win_rates_simple_strategy.txt", "w")
    
    for i in range(3):
        print(str((i+1) * 500000))
        with open("q_data_" + str((i+1) * 500000), "rb") as f:
            rl.Q = pickle.load(f)
            rl.calculatePolicy()
        counts = collections.defaultdict(int)
        for j in range(10000):
            rl.reset()
            winner = rl.evaluatePolicy(rl.pi)
            counts[winner] += 1
        print("Game", j+1, "ends, Player", winner, "wins.")
        print(counts)
        output_file.write(str((i+1) * 500000) + " iterations: " + str(float(counts[0] / 10000)) + "\n")
    output_file.close()
    """

    counts = collections.defaultdict(int)
    start_time = time.time()
    for i in range(5000000):
        rl.reset()
        winner = rl.simulateQLearning()
        counts[winner] += 1
        if (i+1) % 500000 == 0: 
            with open("q_data_"+str(i+1), "wb") as f:
                pickle.dump(rl.Q, f)
            print("Game", i+1, "ends, Player", winner, "wins.")
            print(time.time() - start_time)
    

    rl.calculatePolicy()
    rl.eps = 0

    counts2 = collections.defaultdict(int)
    for i in range(10000):
        rl.reset()
        winner = rl.evaluatePolicy(rl.pi)
        counts2[winner] += 1
        print("Game", i+1, "ends, Player", winner, "wins.")
    print(counts)
    print(counts2)
    
    print(len(rl.Q))
    print(len(rl.pi))
    print("e:", rl.e, "f:" ,rl.f)
    
    counter = collections.defaultdict(int)
    for k,v in rl.Q.items():
        counter[k[0]] += 1
    with open("count.txt", "w") as f:
        for k,v in counter.items():
            f.write(str(k) + ": " + str(v) + "\n")
            f.write(str(rl.pi[k]) + "\n")
    print(sum(list(counter.values())) / len(counter))
    """

if __name__ == "__main__":
    main()
