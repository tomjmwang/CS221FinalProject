
import random
import collections



class Game:
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

    def isEnd(self):
        dead_players = 0
        for player_cards in self.game_state[0]:
            all_inactive = True
            for card in player_cards:
                if card[1] != 2:
                    all_inactive = False
                    break
            if all_inactive:
                dead_players += 1
        if dead_players >= self.num_players - 1:
            return True
        return False

    def reset(self):
        if self.game_state == None:
            random.shuffle(self.cards)
            return
        for cards_in_hand in self.game_state[0]:
            for card in cards_in_hand:
                self.cards.append((card[0], 1))
        random.shuffle(self.cards)

    def getNextLivingPlayer(self, i):
        for j in range(i+1,self.num_players):
            if not self.isDead(j):
                return j
        for j in range(i):
            if not self.isDead(j):
                return j
        return i

    def isDead(self, i):
        dead = True
        for card in self.game_state[0][i]:
            if card[1] != 2:
                dead = False
                break
        return dead

    def checkTruth(self, action):
        all_functions = []
        i = action[1]
        for card in self.game_state[0][i]:
            if card[1] == 1:
                all_functions += self.card_functions[card[0]]
        if action[0] in all_functions:
            return True
        return False

    def loseCard(self, state, i):
        if self.isDead(i):
            return state

        all_cards = list(state[0])
        cards = list(all_cards[i])
        for j,c in enumerate(cards):
            if c[1] == 1:
                cards[j] = (c[0], 2)
                #print("player", i, "lost card", c[0])
                break
        all_cards[i] = tuple(cards)
        return (tuple(all_cards), state[1], state[2], state[3])

    def replaceCard(self, state, i, card):
        all_cards = list(state[0])
        cards = list(all_cards[i])
        for j, c in enumerate(cards):
            if c[0] == card and c[1] == 1:
                removed_card = cards.pop(j)
                cards.append(self.cards.pop(0))
                self.cards.append(removed_card)
                break
        all_cards[i] = tuple(cards)
        return (tuple(all_cards), state[1], state[2], state[3])

    def takeEffect(self, state, action):
        name = action[0]
        i = action[1]
        j = action[2]
        new_coins = list(state[1])
        new_state = state
        if name == "tax":
            new_coins[i] += 3
            #print("player", i, "gained 3 coins")
        elif name == "foreign_aid":
            new_coins[i] += 2
            #print("player", i, "gained 2 coins")
        elif name == "steal":
            if new_coins[j] >= 2:
                new_coins[j] -= 2
                new_coins[i] += 2
            else:
                new_coins[i] += new_coins[j]
                new_coins[j] = 0
            #print("player", i, "stealed from", j)
        elif name == "assassinate":
            new_state = self.loseCard(new_state, j)
            #print("player", i, "assassinated", j)
        else:
            pass
            #print("player", i, "blocked foreign aid of", j)
        return (new_state[0], tuple(new_coins), None, False)




    def getActions(self, i, state):
        if state[2] == None:
            actions = [("tax", i, i), ("income", i, i), ("foreign_aid", i,i)]
            coup_actions = []
            for j in range(self.num_players):
                if j != i and not self.isDead(j):
                    actions.append(("steal",i,j))
                    if state[1][i] >= 3:
                        actions.append(("assassinate",i,j))
                    if state[1][i] >= 7:
                        coup_actions.append(("coup",i,j))
            if state[1][i] >= 10:
                return coup_actions
            return actions + coup_actions

        else:
            if state[2][1] == i:
                return []
            if not state[3]:
                return [("doubt", i, state[2][1]), ("no_doubt", i, None)]
                #return [("no_doubt", i, None)]
            else:
                if state[2][0] == "foreign_aid":
                    return [("block_foreign_aid", i, state[2][1]), ("no_block", i, state[2][1])]
                if state[2][2] != i:
                    return [(None, i, None)]
                if state[2][0] == "steal":
                    return [("block_steal", i, state[2][1]), (None, i, None)]
                else:
                    return [("block_assassinate", i, state[2][1]), (None, i, None)]

    def chooseRandomAction(self, actions):
        return random.choice(actions)

    def chooseBaseLineAction(self,actions,state):
        if actions[0][0] == "doubt":
            eps = 0.2
            if state[0][0][0][0] == state[0][0][0][0] and state[2][0] in self.card_functions[state[0][0][0][0]]:
                return actions[0]
            if random.random() < eps:
                return actions[0]
            else:
                return actions[1]
        else:
            available_functions = []
            for card in state[0][0]:
                if card[1] == 1:
                    available_functions += self.card_functions[card[0]]
            truth_actions = []
            fake_actions = []
            for action in actions:
                if action[0] in available_functions:
                    truth_actions.append(action)
                elif action[0] == "income" or action[0] == "foreign_aid" or action[0] == "no_block" or action[0] == None:
                    truth_actions.append(action)
                elif  action[0] == "coup":
                    truth_actions.append(action)
                else:
                    fake_actions.append(action)
            eps = 0.2
            #print(truth_actions,fake_actions)
            if len(fake_actions) == 0:
                return random.choice(truth_actions)
            if len(truth_actions) == 0:
                return random.choice(fake_actions)
            if random.random() < eps:
                return random.choice(fake_actions)
            else:
                return random.choice(truth_actions)

    def succ(self, action, state):
        i = action[1]
        j = action[2]
        new_player = self.getNextLivingPlayer(i)
        if action[0] == "no_doubt" or action[0] == "no_block":
            return state, new_player
        if action[0] == None:
            new_state = self.takeEffect(state, state[2])
            new_state = (new_state[0], new_state[1], None, False)
            new_player = self.getNextLivingPlayer(self.last_player)
            return new_state, new_player
        new_coins = list(state[1])
        if action[0] == "income":
            new_coins[i] += 1
            new_state = (state[0], tuple(new_coins), None, False)
        elif action[0] == "foreign_aid":
            new_state = (state[0], state[1], action, True)
            self.last_player = i
        elif action[0] == "coup":
            new_coins[i] -= 7
            new_state = self.loseCard(state, j)
            new_state = (new_state[0], tuple(new_coins), None, False)
        elif action[0] == "doubt":
            truth = self.checkTruth(state[2])
            if truth:
                new_state = self.loseCard(state, i)
                new_state = self.replaceCard(new_state, j, self.function_to_char[state[2][0]])
                if len(state[2][0]) > 5 and state[2][0][:5] == "block":
                    new_player = self.getNextLivingPlayer(self.last_player)
                    new_state = (new_state[0], new_state[1], None, False)
                else:
                    if (state[2][0] == "assassinate" or state[2][0] == "steal") and not self.isDead(state[2][2]):
                        new_state = (new_state[0], new_state[1], state[2], True)
                        new_player = state[2][2]
                    else:
                        new_state = self.takeEffect(new_state, state[2])
                        new_player = self.getNextLivingPlayer(self.last_player)
                        new_state = (new_state[0], new_state[1], None, False)
            else:
                new_state = self.loseCard(state, j)
                new_player = self.getNextLivingPlayer(self.last_player)
                if len(state[2][0]) > 5 and state[2][0][:5] == "block":
                    new_state = self.takeEffect(new_state, (state[2][0][6:], state[2][2], state[2][1]))
                new_state = (new_state[0], new_state[1], None, False)
        elif len(action[0]) > 5 and action[0][:5] == "block":
            new_state = (state[0], tuple(new_coins), action, False)
        else:
            self.last_player = i
            if action[0] == "assassinate":
                new_coins[i] -= 3
            new_state = (state[0], tuple(new_coins), action, False)
        return new_state, new_player

    def printState(self, current_player):
        state = self.game_state
        print("Current state:")
        for i,cards in enumerate(state[0]):
            print("player", i, ":")
            for card in cards:
                print(card[0], card[1])
            print("number of coins:", state[1][i])
        print("current action:", state[2], state[3])
        print("current player", current_player)


    def simulateGame(self):
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
                    action = self.chooseBaseLineAction(actions, self.game_state)
                    #action = self.chooseRandomAction(actions)
                else:
                    action = self.chooseRandomAction(actions)
                """
                if action[0] == "no_doubt":
                    print("Player", action[1], "chose to not doubt")
                elif action[0] == "no_block":
                    print("Player", action[1], "chose to not block foreign aid of player", action[2])
                elif action[0] == None:
                    print("Player", action[1], "chose to not block")
                else:
                    print("Player", action[1], "chose action", action[0], "against", action[2])
                """
                new_state, new_player = self.succ(action, self.game_state)
            self.game_state = new_state
            current_player = new_player
            #self.printState(current_player)
            #input("")
            if self.isDead(current_player):
                current_player = self.getNextLivingPlayer(current_player)
            #print("Current state: ", self.game_state)
            if self.isEnd():
                winner = self.getNextLivingPlayer(current_player)
                #print("Player", winner, "wins!")
                break
        return winner


def main():
    cards = [("duke",1), ("duke",1),("assassin",1),("assassin",1),("contessa",1),("contessa",1),("captain",1),("captain",1),("ambassador",1),("ambassador",1)]
    game = Game(cards)
    counts = collections.defaultdict(int)
    for i in range(1000):
        game.reset()
        winner = game.simulateGame()
        counts[winner] += 1
        print("Game", i+1, "ends, Player", winner, "wins.")
    print(counts)


if __name__ == "__main__":
    main()