import collections

import qlearning

class FeatureQLearning(qlearning.QLearning):

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
        self.pi = collections.defaultdict(list)
        self.e = 0
        self.f = 0
        self.last_state = None
        self.accum_reward = 0


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

    def convertGameState(self):
        feature_state = [0 for i in range(6)]
        all_card_functions = []
        living_cards = 0
        for card in self.game_state[0][0]:
            if card[1] == 1:
                all_card_functions += self.card_functions[card[0]]
                living_cards += 1
        for func in all_card_functions:
            if func == "tax":
                feature_state[0] = 1
            if func == "steal":
                feature_state[1] = 1
            if func == "assassinate":
                feature_state[2] = 1
            if func == "block_steal":
                feature_state[3] = 1
            if func == "block_assassinate":
                feature_state[4] = 1

        feature_state[5] = living_cards
        for player_cards in self.game_state[0][1:]:
            temp_cards = []
            living_cards = 0
            for card in player_cards:
                if card[1] == 1:
                    living_cards += 1
            #element1.append(tuple(temp_cards))
            feature_state.append(living_cards)

        feature_state += list(self.game_state[1])

        self.player_state = tuple(feature_state)
        #print(feature_state)

    def calculatePolicy(self):
        self.pi = collections.defaultdict(list)
        for k,v in self.Q.items():
            self.pi[k[0]].append((v, k[1]))
        for k in list(self.pi):
            #print(self.pi[k])
            self.pi[k] = sorted(self.pi[k], reverse=True)
            self.pi[k] = [x[1] for x in self.pi[k]]

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
                        calculated_actions = policy[self.player_state]
                        #print("Current state:", self.game_state)
                        #print("Chosen action:", action)
                        found = False
                        for each_action in calculated_actions:
                            if each_action in actions:
                                action = each_action
                                found = True
                                break
                        if not found:
                            action = self.chooseRandomAction(actions)
                        self.f += 1
                    except KeyError:
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
    rl = FeatureQLearning(cards, num_players=3)


    counts = collections.defaultdict(int)
    for i in range(100000):
        rl.reset()
        winner = rl.simulateQLearning()
        counts[winner] += 1
        print("Game", i+1, "ends, Player", winner, "wins.")

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


if __name__ == "__main__":
    main()











