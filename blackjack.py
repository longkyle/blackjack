#!/usr/bin/env python

"""
Command line version of the classic card game, Blackjack
"""

__author__ = "Kyle Long"
__email__ = "long.kyle@gmail.com"
__date__ = "08/26/2019"
__copyright__ = "Copyright 2019, Kyle Long"
__python_version__ = "3.7.4"


import time
import random
from collections import OrderedDict

YES_LIST = ['y', 'yes', 'Y', 'Yes']
NO_LIST = ['n', 'no', 'N', 'No']
HIT_LIST = ['h', 'hit', 'H', 'Hit']
STAY_LIST = ['s', 'stay', 'S', 'Stay']
DOUBLE_DOWN_LIST = ['d', 'double', 'double down', 'D', 'Double', 'Double Down']
SPLIT_LIST = ['split', 'Split']

MIN_PLAYERS = 1
MAX_PLAYERS = 5
MIN_DECKS = 1
MAX_DECKS = 8

divider = '\n*************************************'


def run():
    """
    Collects initial info such as how many gamblers will be playing, the name
    of each gambler, buy in amounts, and how many decks will be in the shoe.

    Creates the Gamblers, Dealer, & Deck, and then starts the game.
    """
    num_players = None

    print(f'{Format.BOLD}\nWelcome to Kyle\'s Blackjack!\n{Format.END}')

    while num_players is None:
        num_players = input_func('How many people will be playing? (1-5): ',
                                 expected_type=int,
                                 min_value=MIN_PLAYERS,
                                 max_value=MAX_PLAYERS)

    players = []
    for i in range(num_players):
        name_input = input(f'What is the name of Player {i+1}?: ')
        gambler = Gambler(name_input)
        gambler.buy_in()
        players.append(gambler)

    dealer = Dealer()
    players.append(dealer)

    question = 'How many decks would you like to play with?: '
    num_decks = input_func(question,
                           expected_type=int,
                           min_value=MIN_DECKS,
                           max_value=MAX_DECKS)

    deck = Deck(num_decks)
    play(players, deck)

    return


def play(players, deck, first_shuffle=True):
    """
    Creates & shuffles deck/shoe.
    Deal cards.
    Play each hand.
    Figure out which hands are winners.
    Settle up bets.
    Check to see if gamblers want to play again.

    args:
        players (list):         list of all players
        deck (class):           Deck() object
        first_shuffle (bool):   used to wish everybody good luck
                                on the first shuffle of the game
    """
    while len(players) > 1:

        if len(deck.cards) < 52:
            deck.cards = []
            deck.create()
            deck.shuffle()

            shuffle_str = ''
            if first_shuffle:

                if len(players) == 2:
                    shuffle_str = f'Good Luck, {players[0].name}!'
                else:
                    shuffle_str = 'Good Luck, Everyone!'

                shuffle_str = f'{Format.BOLD}{shuffle_str}{Format.END}'

            elif deck.num_decks == 1:
                shuffle_str = 'Re-shuffling Deck'

            else:
                shuffle_str = f'Re-shuffling {deck.num_decks} deck shoe.'

            print(f'\n{shuffle_str}\n')
            time.sleep(1)

        deal(players, deck)
        print_cards(players)

        if not check_dealer_for_blackjack(players):
            play_hands(players, deck)

        determine_winners(players, deck)
        settle_up(players)
        reset_hands(players)
        play_again(players, deck)

    return


def play_hands(players, deck):
    """
    Play each Gambler's hand.

    args:
        players (list):     list of all players
        deck (class):       Deck() object
    """
    for player in players:
        if player.name == 'Dealer':
            continue

        # A gambler may have more than one hand (splits). Play them all
        i = 0
        num_hands = len(player.hands)
        while i < num_hands:
            hand = player.hands[i]
            i += 1

            # No need to continue if hand is a blackjack
            if hand.blackjack:
                continue

            while True:
                # Handle's name differentiaion for multiple hands per gambler
                if num_hands > 1:
                    player_name = f'{player.name} (Hand {i})'
                else:
                    player_name = player.name

                hand_list = HIT_LIST + STAY_LIST
                suggested_dict = {'stay': 's', 'hit': 'h'}

                # Double downs & splits only allowed right after initial deal
                if hand.first_iter:
                    if player.money >= hand.wager * 2:
                        hand_list += DOUBLE_DOWN_LIST
                        suggested_dict['double down'] = 'd'
                    if hand.cards[0].rank == hand.cards[1].rank:
                        hand_list += SPLIT_LIST
                        suggested_dict['split'] = 'split'

                suggested_keys = ", ".join(suggested_dict.keys())
                suggested_values = "/".join(suggested_dict.values())
                question = f'{player_name}, would you like to ' \
                    f'{suggested_keys}? ({suggested_values}): '

                # Ask gambler what action they'd like to take
                user_input = input_func(question,
                                        expected_type=str,
                                        str_options=hand_list,
                                        str_suggestions=suggested_values)

                # Check for 'hit'
                if user_input in HIT_LIST:
                    hand.deal_card(deck)
                    hand.first_iter = False
                    hand.check_busted()
                    print_cards(players)

                # Check for 'stay'
                elif user_input in STAY_LIST:
                    hand.final_value = hand.get_hand_value()[-1]
                    print_cards(players)
                    break

                # Check for 'double down'
                elif user_input in DOUBLE_DOWN_LIST:
                    hand.double_down = True
                    hand.wager *= 2
                    hand.deal_card(deck)
                    hand.first_iter = False
                    hand.final_value = hand.get_hand_value()[-1]
                    dd_str = f'{player_name} has doubled down. ' \
                             f'New wager: ${hand.wager}'
                    print('')
                    print('*' * (len(dd_str) + 6))
                    print(f'*  {dd_str}  *')
                    print('*' * (len(dd_str) + 6))
                    hand.check_busted()
                    print_cards(players)
                    break

                # Check for 'split'
                elif user_input in SPLIT_LIST:
                    split_1 = Hand()
                    split_2 = Hand()

                    # retain the insurance bet
                    if hand.first_iter:
                        split_1.insurance = hand.insurance

                    split_2.cards.append(hand.cards.pop())
                    split_1.cards.append(hand.cards.pop())
                    new_hand = [split_1, split_2]

                    for h in new_hand:
                        h.wager = hand.wager
                        h.deal_card(deck)

                    # insert split hands list in the place of the old hand
                    player.hands = \
                        [new_hand if x == hand else x for x in player.hands]

                    # flatten the list
                    player.hands = flatten_list(player.hands)

                    num_hands = len(player.hands)
                    i -= 1
                    print_cards(players)
                    break

                # Check to see if the hand 'busted'
                if hand.busted:
                    break

    return


def deal(players, deck, test=False):
    """
    Deal 2 cards to each player

    args:
        players (list):     list of all players
        deck (class):       Deck() object
        test (bool):        used for unittests to bypass
                            the need for user input
    """
    for player in players:
        hand = Hand()

        # Get each gambler's wager
        if player.name != 'Dealer':
            if test:
                hand.wager = 25
            else:
                question = f'{player.name}, how much would you like ' \
                           f'to wager? (Balance ${player.money}): '
                hand.wager = input_func(question,
                                        expected_type=int,
                                        min_value=1,
                                        max_value=player.money)

        # Deal 2 cards
        for i in range(2):
            card = deck.cards.pop()

            # First card for dealer is face down
            if i == 0 and player.name == 'Dealer':
                card.hidden = True

            hand.cards.append(card)

        player.hands.append(hand)

    return


def reset_hands(players):
    """
    Remove all players' hands

    args:
        players (list):     list of all players
    """
    for player in players:
        player.hands = []

    return


def check_dealer_for_blackjack(players):
    """
    Check to see if the dealer has blackjack

    args:
        players (list):     list of all players

    returns:
        (bool):             True if dealer has blackjack
                            False if dealer does not have blackjack
    """
    dealer_hand = players[-1].hands[0]

    # Offer gamblers insurance if dealer is showing 'Ace'
    if dealer_hand.cards[1].rank == 'Ace':
        offer_insurance(players)

    dealer_hand.get_hand_value(include_hidden=True)
    dealer_hand.first_iter = False

    if dealer_hand.blackjack:
        dealer_hand.cards[0].hidden = False

        for player in players[:-1]:
            player.hands[0].final_value = player.hands[0].get_hand_value()[0]

        return True

    return False


def offer_insurance(players):
    """
    args:
        players (list):     list of all players
    """
    for player in players[:-1]:
        question = f'{player.name}, would you like insurance? (y/n): '
        insurance = input_func(question,
                               expected_type=str,
                               str_options=YES_LIST + NO_LIST,
                               str_suggestions='y/n')
        if insurance in YES_LIST:
            player.hands[0].insurance = True


def flatten_list(my_list):
    """
    Given a list, possibly nested to any level, return it flattened.

    args:
        my_list (list):     nested list to be flattened

    returns:
        new_list (list):    flattened list
    """
    new_list = []
    for x in my_list:
        if type(x) == list:
            new_list.extend(flatten_list(x))
        else:
            new_list.append(x)

    return new_list


def play_again(players, deck):
    """
    Check to see if each gambler would like to play another game

    args:
        players (list):     list of all players
        deck (class):       Deck() object
    """
    gamblers = players[:-1]
    for gambler in gamblers:
        question = f'{gambler.name}, would you like to play again? (y/n): '
        play_input = input_func(question,
                                expected_type=str,
                                str_options=YES_LIST + NO_LIST,
                                str_suggestions='y/n')

        if play_input in YES_LIST:
            # Buy in for more money if need be
            if gambler.money <= 0:
                question = f'{gambler.name}, your balance is $0. ' \
                            'Would you like to buy in for more money? (y/n): '
                re_buy = input_func(question,
                                    expected_type=str,
                                    str_options=YES_LIST + NO_LIST,
                                    str_suggestions='y/n')
                if re_buy in YES_LIST:
                    gambler.buy_in()
                elif re_buy in NO_LIST:
                    players.remove(gambler)
                    gambler.goodbye()

        elif play_input in NO_LIST:
            players.remove(gambler)
            gambler.goodbye()

    play(players, deck, first_shuffle=False)

    return


def determine_winners(players, deck):
    """
    Determine winners for all gamblers' hands

    args:
        players (list):     list of all players
        deck (class):       Deck() object
    """
    dealer = players[-1]
    dealer_hand = dealer.hands[0]
    dealer_hand.cards[0].hidden = False

    # Play out the dealer's hand
    play_dealer_hand(players, deck, dealer_hand)

    for player in players[:-1]:
        for hand in player.hands:
            if not hand.busted:
                if dealer_hand.busted:
                    hand.win = True
                elif hand.final_value > dealer_hand.final_value:
                    hand.win = True
                elif hand.final_value == dealer_hand.final_value:
                    hand.push = True

    return


def play_dealer_hand(players, deck, dealer_hand):
    """
    Play out the dealer's hand

    args:
        players (list):         list of all players
        deck (class):           Deck() object
        dealer_hand (class):    the dealer's hand
    """

    # Get the initial value of the dealer's 2 card hand
    while True:
        values = dealer_hand.get_hand_value()

        # dealer must hit a soft 17
        stand_value = 17
        if len(values) == 2:
            stand_value = 18

        value = values[-1]

        # Dealer stands
        time.sleep(1)
        if value >= stand_value:
            dealer_hand.final_value = value

            if value > 21:
                dealer_hand.busted = True

            print_cards(players, show=True)
            break

        # Dealer hits
        if value < stand_value:
            print_cards(players, show=True)
            dealer_hand.deal_card(deck)

    return


def settle_up(players):
    """
    Settle up everybody's bets.

    args:
        players (list):     list of all players
    """

    dealer_hand = players[-1].hands[0]
    # Notify everybody that they've lost if the dealer has blackjack
    if dealer_hand.blackjack:
        print(divider)
        print('Sorry! Dealer had Blackjack.\n')

    for player in players[:-1]:
        num_hands = len(player.hands)
        i = 0
        while i < num_hands:
            hand = player.hands[i]
            i += 1

            # Handle's name differentiaion for multiple hands per gambler
            if num_hands > 1:
                player_name = f'{player.name} (Hand {i})'
            else:
                player_name = player.name

            winnings = 0

            # Insurnace bets
            if hand.insurance:
                if dealer_hand.blackjack:
                    winnings += hand.wager * 0.5
                else:
                    winnings -= hand.wager * 0.5

                # Format winnings
                if winnings % 1 == 0:
                    winnings = int(winnings)

            # Blackjack pays 3/2
            if hand.blackjack:
                winnings += hand.wager * 1.5

                # Format winnings
                if winnings % 1 == 0:
                    winnings = int(winnings)

                print(f'{Format.BOLD}{Format.GREEN}{player_name} '
                      f'got Blackjack! Won ${winnings}{Format.END}')

            # Do nothing on push
            elif hand.push:
                print(f'{Format.BOLD}{player_name} pushed')

            # Payout even money on win
            elif hand.win:
                winnings += hand.wager
                print(f'{Format.BOLD}{Format.GREEN}{player_name} '
                      f'won ${winnings}{Format.END}')

            # Subtract wager on loss
            else:
                winnings -= hand.wager
                print(f'{Format.BOLD}{Format.RED}{player_name} '
                      f'lost ${abs(winnings)}{Format.END}')

            # Format player.money
            player.money += winnings
            if player.money % 1 == 0:
                player.money = int(player.money)

            # Print new balance
            print(f'{player.name}\'s Balance: ${player.money}\n')

    print(divider)

    return


def print_cards(players, show=False):
    """
    Prints all players' hands

    args:
        players (list):     list of all players
        show (bool):        determines if dealer is showing
                            hidden card or not
    """
    print(divider)

    for player in players:
        num_hands = len(player.hands)
        for i in range(num_hands):
            hand = player.hands[i]
            counter = i + 1

            card_values = hand.get_hand_value()

            # format hand values
            if hand.final_value:
                values_str = hand.final_value
            else:
                num_values = len(card_values)
                values_str = ''
                for i in range(num_values):
                    values_str += str(card_values[i])
                    if (i + 1) < num_values:
                        values_str += ' or '

            # add extra hand information
            info = ''
            if hand.blackjack:
                info = ' (Blackjack!)'
            if hand.busted:
                info = ' (Busted)'

            # change verb to 'showing' if dealer has hidden card
            verb = 'has'
            if player.name == 'Dealer' and not show:
                verb = 'showing'

            # print value of each hand
            if num_hands > 1:
                print(f'{Format.BOLD}{player.name} (Hand {counter}) '
                      f'{verb}: {values_str}{info}{Format.END}')
            else:
                print(f'{Format.BOLD}{player.name} {verb}: '
                      f'{values_str}{info}{Format.END}')

            # print each card
            for card in hand.cards:
                print(card.get_card_str())

            print('')

    return


def input_func(question, expected_type=None,
               min_value=None, max_value=None,
               str_options=None, str_suggestions=None):
    """
    Handle user input for any generic question.

    args:
        question (str):         Question to be asked to the user
        expected_type (class):  str, int
        min_value (int):        minimum acceptable input value
        max_value (int):        maximum acceptable input value
        str_options (list):     list of acceptable user responses
        str_suggestions (list): list of suggested responses

    returns:
        converted_input (int):  converts user inputed str to an int
        user_input (str):       string input from user

    """
    while True:
        user_input = input(question)

        if expected_type == int:
            try:
                converted_input = int(user_input)
            except ValueError:
                print(f'Invalid input. Expected an integer between '
                      f'{min_value}-{max_value}')
                continue

            if not (min_value <= converted_input <= max_value):
                print(f'Invalid input. Expected an integer between '
                      f'{min_value}-{max_value}')
                continue

            return converted_input

        elif expected_type == str:
            if user_input not in str_options:
                print(f'Invalid input. Expected one of the following: '
                      f'({str_suggestions})')
                continue

            return user_input


class Deck():
    """
    Class creates and shuffles card deck.

    args:
        num_decks (int):    number of decks to be used in the shoe
    """

    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        self.cards = []
        self.suits = ('Hearts', 'Diamonds', 'Clubs', 'Spades')
        self.ranks = OrderedDict([('Two', 2), ('Three', 3), ('Four', 4),
                                  ('Five', 5), ('Six', 6), ('Seven', 7),
                                  ('Eight', 8), ('Nine', 9), ('Ten', 10),
                                  ('Jack', 10), ('Queen', 10), ('King', 10),
                                  ('Ace', 1)])

    def create(self):
        for i in range(self.num_decks):
            for suit in self.suits:
                for rank in self.ranks:
                    value = self.ranks[rank]
                    self.cards.append(Card(suit, rank, value))
        return

    def shuffle(self):
        random.shuffle(self.cards)
        return


class Hand():
    """
    Class for holding all single hand information.
    """

    def __init__(self):
        self.cards = []
        self.wager = None
        self.blackjack = False
        self.win = False
        self.push = False
        self.double_down = False
        self.split = []
        self.insurance = False
        self.busted = False
        self.final_value = None
        self.first_iter = True

    def deal_card(self, deck, card=None):
        """
        Deals a single card to the hand. Card can be
        user specified for testing purposes using the
        'card' argument.

        i.e. card=Card("Hearts", "King", 10)

        args:
            deck (class):   Deck() object
            card (class):   Card() object
        """
        if card:
            self.cards.append(card)
        else:
            self.cards.append(deck.cards.pop())
        return

    def check_busted(self):
        """
        Checks to see if the hand has busted (over 21).
        """
        hand_value = self.get_hand_value()
        busted = True
        for cv in hand_value:
            if cv <= 21:
                busted = False

        if busted:
            self.final_value = hand_value[-1]
            self.busted = busted

        return

    def get_hand_value(self, include_hidden=False):
        """
        Determine all possible values for a given hand.

        args:
            include_hidden (bool):  determines whether or not to
                                    include the dealer's hidden
                                    card.

        returns:
            values (list):          a list of possible hand values
        """
        cards = []
        cards.extend(self.cards)

        values = [0]
        for card in cards:
            if card.hidden and not include_hidden:
                continue

            # handles aces
            v = card.value
            if v == 1:
                for i in range(len(values)):
                    values[i] += v
                    values.append(values[i] + 10)
            else:
                for i in range(len(values)):
                    values[i] += v

        # remove duplicate values & values over 21. sort list.
        new_values = sorted(list(set(i for i in values if i <= 21)))
        if not new_values:
            values = [sorted(list(set(values)))[0]]
        else:
            values = new_values

        # determine if hand is 'blackjack'
        if self.first_iter and 21 in values:
            self.blackjack = True
            self.final_value = 21

        return values


class Card():
    """
    Holds all single card information.

    args:
        suit (str):     Hearts, Diamonds, Spades, Clubs
        rank (str):     Two, Three, ... , Queen, King, Ace
        value (int):    2, 3, ... , 10, 10, 1
    """

    def __init__(self, suit, rank, value):
        self.suit = suit
        self.rank = rank
        self.value = value
        self.hidden = False

    def get_card_str(self):
        """
        returns:
            (str):      String representation of card
        """
        if self.hidden:
            return '**'
        else:
            return f'{self.rank} of {self.suit}'


class Player():
    """
    Player class holds all Player hands & Player name.

    args:
        name (str):     name of the player
    """
    def __init__(self, name):
        self.name = name
        self.hands = []


class Dealer(Player):
    """
    Dealer Class inherits from Player and automatically
    names itself 'Dealer'
    """
    def __init__(self):
        Player.__init__(self, name='Dealer')


class Gambler(Player):
    """
    Gambler Class holds each Gambler's total chip value.
    Handles buy-ins and a salutation when the game is done.

    args:
        name (str):     name of the gambler
    """
    def __init__(self, name):
        Player.__init__(self, name)
        self.money = None

    def buy_in(self, test=False):
        """
        args:
            test (bool):    used for unittests to bypass
                            the need for user input
        """
        if test:
            self.money = 500
        else:
            question = f'{self.name}, how much would you like ' \
                        'to buy in for? (500 max): '
            self.money = input_func(question,
                                    expected_type=int,
                                    min_value=1,
                                    max_value=500)
        return

    def goodbye(self):
        print(f'\n{Format.BOLD}Goodbye, {self.name}. '
              f'Thanks for playing!{Format.END}')

        return


class Format():
    """
    Handles text formatting for command line printing.
    """
    GREEN = '\033[32m'
    RED = '\033[31m'
    BOLD = '\033[1m'
    END = '\033[0m'


if __name__ == "__main__":
    run()
