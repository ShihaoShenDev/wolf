import sys
import os
import unittest
from collections import Counter

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wolf.server.game.engine import Game, GamePhase
from wolf.server.game.roles import (
    Werewolf, Villager, Seer, Witch, Hunter, Guard, Idiot, Knight, SkillType, Team
)

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.player_ids = [f"player_{i}" for i in range(12)]
        self.game = Game(self.player_ids)
        self.game.start()

    def test_initial_roles(self):
        wolves = [p for p in self.game.players.values() if isinstance(p.role, Werewolf)]
        villagers = [p for p in self.game.players.values() if isinstance(p.role, Villager)]
        gods = [p for p in self.game.players.values() if p.role.team == Team.GOOD and not isinstance(p.role, Villager)]
        
        self.assertEqual(len(wolves), 4)
        self.assertEqual(len(villagers), 4)
        self.assertEqual(len(gods), 4)

    def test_night_phase_basic(self):
        # Identify roles
        wolves = [p for p in self.game.players.values() if isinstance(p.role, Werewolf)]
        villagers = [p for p in self.game.players.values() if isinstance(p.role, Villager)]
        
        wolf_id = wolves[0].player_id
        target_id = villagers[0].player_id
        
        # Wolf kill
        success, _ = self.game.process_night_action(wolf_id, target_id, SkillType.KILL)
        self.assertTrue(success)
        
        # Resolve night
        deaths = self.game.resolve_night()
        self.assertIn(target_id, deaths)
        self.assertEqual(self.game.phase, GamePhase.DAY)
        self.assertFalse(self.game.players[target_id].is_alive)

    def test_voting_execution(self):
        self.game.phase = GamePhase.DAY
        
        # Get alive players
        alive_players = [pid for pid, p in self.game.players.items() if p.is_alive]
        voter_1 = alive_players[0]
        voter_2 = alive_players[1]
        target = alive_players[2]
        
        # Vote
        self.game.process_day_action(voter_1, target, "VOTE")
        self.game.process_day_action(voter_2, target, "VOTE")
        
        # Resolve vote
        executed_id, msg = self.game.resolve_vote()
        self.assertEqual(executed_id, target)
        self.assertFalse(self.game.players[target].is_alive)

    def test_vote_tie(self):
        self.game.phase = GamePhase.DAY
        alive_players = [pid for pid, p in self.game.players.items() if p.is_alive]
        
        voter_1 = alive_players[0]
        target_1 = alive_players[2]
        
        voter_2 = alive_players[1]
        target_2 = alive_players[3]
        
        self.game.process_day_action(voter_1, target_1, "VOTE")
        self.game.process_day_action(voter_2, target_2, "VOTE")
        
        executed_id, msg = self.game.resolve_vote()
        self.assertIsNone(executed_id)
        self.assertIn("tie", msg)
        self.assertTrue(self.game.players[target_1].is_alive)
        self.assertTrue(self.game.players[target_2].is_alive)

    def test_hunter_shoot(self):
        self.game.phase = GamePhase.DAY
        # Manually assign Hunter
        hunter_id = self.player_ids[0]
        self.game.players[hunter_id].role = Hunter()
        self.game.players[hunter_id].role.skills = {SkillType.SHOOT}
        
        target_id = self.player_ids[1]
        
        # Kill Hunter
        self.game.players[hunter_id].is_alive = False
        self.game.players[hunter_id].can_shoot = True # Simulate death trigger
        
        # Shoot
        success, msg = self.game.process_day_action(hunter_id, target_id, "SHOOT")
        self.assertTrue(success)
        self.assertFalse(self.game.players[target_id].is_alive)
        self.assertFalse(self.game.players[hunter_id].can_shoot) # Should be used

    def test_idiot_flip(self):
        # Manually assign Idiot
        idiot_id = self.player_ids[0]
        self.game.players[idiot_id].role = Idiot()
        
        self.game.phase = GamePhase.DAY
        
        # Vote out Idiot
        voter_id = self.player_ids[1]
        self.game.process_day_action(voter_id, idiot_id, "VOTE")
        
        executed_id, msg = self.game.resolve_vote()
        self.assertEqual(executed_id, idiot_id)
        self.assertTrue(self.game.players[idiot_id].is_alive) # Should be alive
        self.assertTrue(self.game.players[idiot_id].is_idiot_flipped)
        
        # Idiot tries to vote
        success, msg = self.game.process_day_action(idiot_id, voter_id, "VOTE")
        self.assertFalse(success)
        self.assertIn("cannot vote", msg)

    def test_knight_duel_wolf(self):
        # Assign Knight and Wolf
        knight_id = self.player_ids[0]
        wolf_id = self.player_ids[1]
        
        self.game.players[knight_id].role = Knight()
        self.game.players[knight_id].role.skills = {SkillType.DUEL}
        self.game.players[wolf_id].role = Werewolf()
        
        self.game.phase = GamePhase.DAY
        
        success, msg = self.game.process_day_action(knight_id, wolf_id, "DUEL")
        self.assertTrue(success)
        self.assertIn("Wolf", msg)
        self.assertFalse(self.game.players[wolf_id].is_alive)
        self.assertTrue(self.game.players[knight_id].is_alive)
        self.assertNotIn(SkillType.DUEL, self.game.players[knight_id].role.skills)

    def test_knight_duel_good(self):
        # Assign Knight and Villager
        knight_id = self.player_ids[0]
        villager_id = self.player_ids[1]
        
        self.game.players[knight_id].role = Knight()
        self.game.players[knight_id].role.skills = {SkillType.DUEL}
        self.game.players[villager_id].role = Villager()
        
        self.game.phase = GamePhase.DAY
        
        success, msg = self.game.process_day_action(knight_id, villager_id, "DUEL")
        self.assertTrue(success)
        self.assertIn("failed", msg)
        self.assertTrue(self.game.players[villager_id].is_alive)
        self.assertFalse(self.game.players[knight_id].is_alive)

    def test_win_condition_wolf(self):
        # Kill all villagers
        for p in self.game.players.values():
            if isinstance(p.role, Villager):
                p.is_alive = False
        
        winner = self.game.check_win()
        self.assertEqual(winner, Team.WEREWOLF)
        self.assertEqual(self.game.phase, GamePhase.ENDED)

    def test_win_condition_good(self):
        # Kill all wolves
        for p in self.game.players.values():
            if p.role.team == Team.WEREWOLF:
                p.is_alive = False
        
        winner = self.game.check_win()
        self.assertEqual(winner, Team.GOOD)
        self.assertEqual(self.game.phase, GamePhase.ENDED)

    def test_next_phase(self):
        self.game.phase = GamePhase.DAY
        self.game.next_phase()
        self.assertEqual(self.game.phase, GamePhase.NIGHT)
        self.assertEqual(self.game.round, 2)
        self.assertEqual(len(self.game.night_actions), 0)

if __name__ == "__main__":
    unittest.main()
