#!/usr/bin/env python

"""
unittests for blackjack.py
"""

__author__ = "Kyle Long"
__email__ = "long.kyle@gmail.com"
__date__ = "08/26/2019"
__copyright__ = "Copyright 2019, Kyle Long"
__python_version__ = "3.7.4"


import unittest
import blackjack as bj
from blackjack import Card, Deck, Hand, Dealer, Gambler


class TestBlackjack(unittest.TestCase):

    def test_deal_and_reset_hands(self):
        """
        Make sure deal() gives each player 2 cards and
        that it removes 2 cards from the deck for each player.
        Make sure reset_hands clears each players hands.
        """

        # create 3 gamblers
        players = []
        total_players = 4
        for i in range(total_players - 1):
            gambler = bj.Gambler(f'Player {i+1}')
            gambler.money = 500
            players.append(gambler)

        # create dealer
        dealer = bj.Dealer()
        players.append(dealer)

        # create, shuffle, & deal deck
        num_decks = 1
        deck = bj.Deck(num_decks=num_decks)
        deck.create()
        deck.shuffle()
        bj.deal(players, deck, test=True)

        # check that each player got 2 cards
        for i in range(total_players):
            self.assertEqual(len(players[i].hands[0].cards), 2)

        # check that Deck.deal() removed 2*num_players cards from deck
        self.assertEqual(num_decks * 52 - total_players * 2, len(deck.cards))

        # reset hands & check for accuracy
        bj.reset_hands(players)
        result = False
        for p in players:
            if p.hands:
                result = True
        self.assertFalse(result)

    def test_check_dealer_for_blackjack(self):
        """
        Test that check_dealer_for_blackjack() function accurately
        recognizes when the dealer has been dealt a blackjack.
        """

        # create dealer & hand
        dealer = bj.Dealer()
        hand = bj.Hand()
        dealer.hands.append(hand)

        # 10, ace check
        card1 = bj.Card('Hearts', '*', 10)
        card2 = bj.Card('Hearts', '*', 1)
        hand.cards.append(card1)
        hand.cards.append(card2)
        self.assertTrue(bj.check_dealer_for_blackjack([dealer]))

        # ace, 10 check
        hand.first_iter = True
        hand.blackjack = False
        dealer.hands[0].cards[0].value = 1
        dealer.hands[0].cards[1].value = 10
        self.assertTrue(bj.check_dealer_for_blackjack([dealer]))

        # ace, 5 check
        hand.first_iter = True
        hand.blackjack = False
        dealer.hands[0].cards[1].value = 5
        self.assertFalse(bj.check_dealer_for_blackjack([dealer]))

    def test_flatten_list(self):
        """
        Create nested list & flatten it using flatten_list.
        Check for accuracy.
        """
        my_list = [1, [2, [3, 3], 2], 1, [2, 2], 1]
        result = bj.flatten_list(my_list)
        self.assertEqual(result, [1, 2, 3, 3, 2, 1, 2, 2, 1])

    def test_determine_winners(self):
        """
        Test that the dealer hits at the appropriate times and
        that winning hands are appropriated updated as such.
        """

        # setup deck
        deck = Deck()
        deck.create()
        deck.shuffle()

        # setup gambler, dealer & hands
        dealer = Dealer()
        dealer_hand = Hand()
        dealer.hands.append(dealer_hand)
        gambler = Gambler("Test")
        gambler_hand = Hand()
        gambler.hands.append(gambler_hand)
        players = [gambler, dealer]

        # must hit a soft 17 (A, 6)
        gambler_hand.final_value = 20
        dealer_hand.cards.append(Card('Hearts', 'Ace', 1))
        dealer_hand.cards.append(Card('Hearts', 'Six', 6))
        bj.determine_winners(players, deck)
        self.assertTrue(len(dealer_hand.cards) > 2)

        # must hit on 16 or less (K, 6)
        self.reset_hand_attrs(dealer_hand)
        dealer_hand.cards.append(Card('Hearts', 'King', 10))
        dealer_hand.cards.append(Card('Hearts', 'Six', 6))
        bj.determine_winners(players, deck)
        self.assertTrue(len(dealer_hand.cards) > 2)

        # check dealer bust (K, 6, J)
        dealer_hand.cards.pop()
        dealer_hand.cards.append(Card('Hearts', 'Jack', 10))
        bj.determine_winners(players, deck)
        self.assertTrue(dealer_hand.busted)
        self.assertTrue(gambler_hand.win)

        # check dealer stands on 17 (K, 7)
        self.reset_hand_attrs(dealer_hand)
        dealer_hand.cards.append(Card('Hearts', 'King', 10))
        dealer_hand.cards.append(Card('Hearts', 'Seven', 7))
        bj.determine_winners(players, deck)
        self.assertTrue(len(dealer_hand.cards) == 2)

        # gambler wins with 20 to dealer's 17
        self.assertTrue(gambler_hand.win)

        # check dealer stands on soft 18 (Ace, 7)
        self.reset_hand_attrs(dealer_hand)
        dealer_hand.cards.append(Card('Hearts', 'Ace', 1))
        dealer_hand.cards.append(Card('Hearts', 'Seven', 7))
        bj.determine_winners(players, deck)
        self.assertTrue(len(dealer_hand.cards) == 2)

    def test_settle_up(self):
        """
        Test that settle_up() function accurately updates
        each players .money attribute for various outcomes.
        """

        # setup players
        dealer = Dealer()
        player = Gambler('Test')
        players = [player, dealer]

        # setup hands
        dealer_hand = Hand()
        dealer.hands.append(dealer_hand)
        hand = Hand()
        player.hands.append(hand)

        # check loss
        player.money = 500
        hand.wager = 100
        bj.settle_up(players)
        self.assertEqual(player.money, 400)

        # check win
        hand.win = True
        bj.settle_up(players)
        self.assertEqual(player.money, 500)

        # check push
        hand.win = False
        hand.push = True
        bj.settle_up(players)
        self.assertEqual(player.money, 500)

        # check insurance w/ dealer blackjack
        dealer_hand.blackjack = True
        hand.insurance = True
        bj.settle_up(players)
        self.assertEqual(player.money, 550)
        hand.insurance = False
        bj.settle_up(players)
        self.assertEqual(player.money, 550)

        # check insurance w/o dealer blackjack
        dealer_hand.blackjack = False
        hand.insurance = True
        bj.settle_up(players)
        self.assertEqual(player.money, 500)
        hand.insurance = False
        bj.settle_up(players)
        self.assertEqual(player.money, 500)

        # check Blackjack
        hand.push = False
        hand.blackjack = True
        bj.settle_up(players)
        self.assertEqual(player.money, 650)

        # check blackjack with fractional dollars
        hand.wager = 5
        bj.settle_up(players)
        self.assertEqual(player.money, 657.5)

        # check dealer blackjack
        dealer_hand.blackjack = True
        hand.blackjack = False
        bj.settle_up(players)
        self.assertEqual(player.money, 652.5)

    def reset_hand_attrs(self, hand):
        """
        Non-test method that resets a hand to it's original
        state. Used in other test methods for cleanup
        in between similar assert calls.

        args:
            hand (class):   Hand() object
        """
        hand.cards = []
        hand.wager = None
        hand.blackjack = False
        hand.win = False
        hand.push = False
        hand.double_down = False
        hand.split = []
        hand.busted = False
        hand.final_value = None
        hand.first_iter = True


class TestCard(unittest.TestCase):

    def test_get_card_str(self):
        """
        Test that get_card_str() returns the appropriate
        str representation of a card. Also test that it works
        with hidden cards.
        """
        card = Card('Hearts', 'King', 10)
        self.assertEqual(card.get_card_str(), 'King of Hearts')

        card.hidden = True
        self.assertEqual(card.get_card_str(), '**')


class TestDeck(unittest.TestCase):

    def test_deck_size(self):
        """
        Make sure each deck is exactly 52 cards
        Check for each shoe size.
        """
        for i in range(bj.MIN_DECKS, bj.MAX_DECKS + 1):
            deck = Deck(num_decks=i)
            deck.create()
            self.assertEqual(len(deck.cards), 52 * i)

    def test_shuffle(self):
        """
        Make sure Deck.shuffle is randomized
        """
        deck1 = Deck(num_decks=1)
        deck2 = Deck(num_decks=1)
        deck1.shuffle()
        deck2.shuffle()
        self.assertNotEqual(deck1, deck2)


class TestHand(unittest.TestCase):

    def test_deal_card(self):
        """
        Test that dealing a card removes 1 card
        from the deck and adds 1 card to the hand.
        """
        self.deck = Deck(num_decks=1)
        self.deck.create()
        self.deck.shuffle()
        self.hand = Hand()
        self.hand.deal_card(self.deck)
        self.assertEqual(len(self.deck.cards), 51)
        self.assertEqual(len(self.hand.cards), 1)

    def test_check_busted(self):
        """
        Check to see if a hand is a bust (> 21) or not.
        """

        # hand is busted
        self.hand = Hand()
        self.hand.cards.append(Card('Hearts', 'King', 10))
        self.hand.cards.append(Card('Hearts', 'Three', 3))
        self.hand.cards.append(Card('Hearts', 'Jack', 10))
        self.hand.check_busted()
        self.assertTrue(self.hand.busted)

        # hand is not busted
        self.hand = Hand()
        self.hand.cards.append(Card('Hearts', 'King', 10))
        self.hand.cards.append(Card('Hearts', 'Three', 3))
        self.hand.cards.append(Card('Hearts', 'Six', 6))
        self.hand.check_busted()
        self.assertFalse(self.hand.busted)

    def test_get_hand_value(self):
        """
        Make sure get_hand_value() returns accurate hand values.
        """

        # test hand values with Aces
        self.hand = Hand()
        self.hand.cards.append(Card('Hearts', 'Ace', 1))
        self.hand.cards.append(Card('Spades', 'Ace', 1))
        self.hand.cards.append(Card('Hearts', 'Six', 6))
        hand_values = self.hand.get_hand_value()
        self.assertEqual(hand_values, [8, 18])

        # test hand values with hidden card (Dealer)
        self.hand.cards[2].hidden = True
        hand_values = self.hand.get_hand_value()
        self.assertEqual(hand_values, [2, 12])

        # test hand values with hidden card included (Dealer)
        hand_values = self.hand.get_hand_value(include_hidden=True)
        self.assertEqual(hand_values, [8, 18])


class TestGambler(unittest.TestCase):

    def test_buy_in(self):
        """
        Make sure buy_in() adds money to the .money attribute.
        """
        self.gambler = Gambler("Test")
        self.gambler.buy_in(test=True)
        self.assertEqual(self.gambler.money, 500)


if __name__ == '__main__':
    unittest.main()
