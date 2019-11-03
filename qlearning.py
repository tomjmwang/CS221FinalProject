import game
import collections
import random

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
        if self.isEndState(new_state):
            return 1000.0
        return 0.0

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
        state_to_q = collections.defaultdict(float)
        for k,v in self.Q.items():
            #if k[0] not in state_to_q:
            #    self.pi[k[0]] = k[1]
            #    state_to_q[k[0]] = v
            #else:
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
                    action = self.chooseRandomAction(actions)
                new_state, new_player = self.succ(action, self.game_state)
            if current_player == 0:
                old_state = self.game_state
                r = self.reward(old_state, action, new_state)
                next_max_q = 0
                if len(self.Q) > 0:
                    next_max_q = max(list(self.Q.values()))
                self.Q[(self.player_state,action)] = max_q + self.alpha*(r + self.discount*next_max_q - max_q)
            self.game_state = new_state
            current_player = new_player
            if self.isDead(current_player):
                current_player = self.getNextLivingPlayer(current_player)
            #print("Current state: ", self.game_state)
            if self.isEnd():
                winner = self.getNextLivingPlayer(current_player)
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
                        self.f += 1
                    except:
                        self.e += 1
                        action = self.chooseRandomAction(actions)
                        #print("errorfound")
                else:
                    action = self.chooseRandomAction(actions)
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
    rl = QLearning(cards)
    counts = collections.defaultdict(int)
    for i in range(30000):
        rl.reset()
        winner = rl.simulateQLearning()
        counts[winner] += 1
        print("Game", i+1, "ends, Player", winner, "wins.")
    

    rl.calculatePolicy()
    rl.eps = 0

    counts2 = collections.defaultdict(int)
    for i in range(1000):
        rl.reset()
        winner = rl.evaluatePolicy(rl.pi)
        counts2[winner] += 1
        print("Game", i+1, "ends, Player", winner, "wins.")
    print(counts)
    print(counts2)
    print(len(rl.Q))
    print(len(rl.pi))
    print("e:", rl.e, "f:" ,rl.f)

if __name__ == "__main__":
    main()