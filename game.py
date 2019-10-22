
import random



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
        if dead_players == self.num_players - 1:
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
                print("player", i, "lost card", c[0])
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
            print("player", i, "gained 3 coins")
        elif name == "foreign_aid":
            new_coins[i] += 2
            print("player", i, "gained 2 coins")
        elif name == "steal":
            if new_coins[j] >= 2:
                new_coins[j] -= 2
                new_coins[i] += 2
            else:
                new_coins[i] += new_coins[j]
                new_coins[j] = 0
            print("player", i, "stealed from", j)
        elif name == "assassinate":
            new_state = self.loseCard(new_state, j)
            print("player", i, "assassinated", j)
        else:
            print("player", i, "blocked foreign aid of", j)
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
                return [("doubt", i, state[2][1]), (None, i, None)]
            else:
                if state[2][0] == "foreign_aid":
                    return [("block_foreign_aid", i, state[2][1]), (None, i, None)]
                if state[2][2] != i:
                    return [(None, i, None)]
                if state[2][0] == "steal":
                    return [("block_steal", i, state[2][1]), (None, i, None)]
                else:
                    return [("block_assassinate", i, state[2][1]), (None, i, None)]

    def chooseRandomAction(self, actions):
        return random.choice(actions)

    def succ(self, action, state):
        i = action[1]
        j = action[2]
        new_player = self.getNextLivingPlayer(i)
        if action[0] == None:
            return state, new_player
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
                    pass
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
        else:
            if action[0] != "block_foreign_aid":
                self.last_player = i
            if action[0] == "assassinate":
                new_coins[i] -= 3
            new_state = (state[0], tuple(new_coins), action, False)
        return new_state, new_player




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
        print("initial state: ", self.game_state)
        current_player = self.starting_player
        while True:
            actions = self.getActions(current_player, self.game_state)
            if len(actions) == 0:
                new_player = self.getNextLivingPlayer(self.game_state[2][1])
                new_state = self.takeEffect(self.game_state, self.game_state[2])
            else:
                action = self.chooseRandomAction(actions)
                if action[0] == None:
                    print("Player", action[1], "chose to not doubt")
                else:
                    print("Player", action[1], "chose action", action[0], "against", action[2])
                new_state, new_player = self.succ(action, self.game_state)
            self.game_state = new_state
            current_player = new_player
            if self.isDead(current_player):
                current_player = self.getNextLivingPlayer(current_player)
            #print("Current state: ", self.game_state)
            if self.isEnd():
                break
        return self.game_state


def main():
    cards = [("duke",1), ("duke",1),("assassin",1),("assassin",1),("contessa",1),("contessa",1),("captain",1),("captain",1),("ambassador",1),("ambassador",1),]
    game = Game(cards)
    game.reset()

    game.simulateGame()

if __name__ == "__main__":
    main()