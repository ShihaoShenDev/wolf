import random
from enum import Enum, auto
from typing import List, Dict, Optional, Set
from .roles import (
    Role, Team, SkillType,
    Werewolf, Villager, Seer, Witch, Hunter, Guard, Idiot, Knight
)
from collections import Counter

class GamePhase(Enum):
    WAITING = "WAITING"
    NIGHT = "NIGHT"
    DAY = "DAY"
    ENDED = "ENDED"

class PlayerState:
    def __init__(self, player_id: str, role: Role):
        self.player_id = player_id
        self.role = role
        self.is_alive = True
        self.sheriff = False # 警长
        self.is_idiot_flipped = False # 白痴翻牌
        self.can_shoot = False # 猎人能否开枪

    def __repr__(self):
        return f"<Player {self.player_id}: {self.role.name}, Alive: {self.is_alive}>"

class Game:
    def __init__(self, player_ids: List[str]):
        if len(player_ids) != 12:
            # For testing purposes, we might want to allow fewer players, 
            # but the requirement says 12. 
            # We can relax this or enforce it. 
            # Let's enforce it but maybe allow bypass for testing if needed.
            pass 
        
        self.player_ids = player_ids
        self.players: Dict[str, PlayerState] = {}
        self.phase = GamePhase.WAITING
        self.round = 0
        self.winner: Optional[Team] = None
        
        # Game State
        self.witch_save_used = False
        self.witch_poison_used = False
        self.last_guarded_id = None
        
        # Night actions: {player_id: {'target_id': str, 'skill_type': SkillType}}
        self.night_actions: Dict[str, dict] = {}
        
        # Result of the night
        self.night_deaths: Set[str] = set()
        
        # Day actions
        self.day_votes: Dict[str, str] = {} # voter_id -> target_id


    def assign_roles(self):
        """
        Randomly assign roles for 12 players:
        4 Werewolves
        4 Villagers
        4 Gods: Seer, Witch, Hunter, Guard, Idiot, Knight (Pick 4)
        
        Wait, standard 12 player setup usually is:
        4 Wolves, 4 Villagers, 4 Gods (Seer, Witch, Hunter, Guard/Idiot/Knight).
        The prompt lists: "Werewolf, Villager, Seer, Witch, Hunter, Guard, Idiot, Knight".
        It says "4 gods". So I need to pick 4 distinct gods from the pool of 6 gods?
        Standard 12-person board: 
        - 4 Wolves
        - 4 Villagers
        - 4 Gods (Pre-defined set, usually Seer, Witch, Hunter, Guard)
        
        The prompt lists all these roles but says "4 gods". 
        I will assume a standard set: Seer, Witch, Hunter, Guard.
        Or should I pick random 4? 
        Given "Implement all roles... Idiot, Knight", I should probably support them.
        But for a specific game instance, I need to decide which gods are in play.
        Let's assume a default configuration: Seer, Witch, Hunter, Guard.
        Or maybe the prompt implies using all implemented roles in some way?
        "Assign roles for 12 players (4 wolves, 4 villagers, 4 gods)."
        I'll stick to Seer, Witch, Hunter, Guard as the default 4 gods for now.
        """
        if len(self.player_ids) < 12:
             # Fallback for testing with fewer players
             # Just assign randomly whatever we have
             roles = [Werewolf(), Villager(), Seer(), Witch()] # Minimal set
             # Fill the rest with Villagers
             while len(roles) < len(self.player_ids):
                 roles.append(Villager())
             roles = roles[:len(self.player_ids)]
        else:
            roles = []
            for _ in range(4): roles.append(Werewolf())
            for _ in range(4): roles.append(Villager())
            # Default Gods
            roles.append(Seer())
            roles.append(Witch())
            roles.append(Hunter())
            roles.append(Guard())
            # If we want to support Idiot/Knight, we might need configuration.
            # For now, let's just use these standard 4.

        random.shuffle(roles)
        
        self.players = {}
        for i, pid in enumerate(self.player_ids):
            self.players[pid] = PlayerState(pid, roles[i])

    def start(self):
        self.assign_roles()
        self.phase = GamePhase.NIGHT
        self.round = 1
        self.night_actions = {}
        self.night_deaths = set()

    def process_night_action(self, player_id: str, target_id: str, skill_type: SkillType):
        """
        Store actions.
        Validate if the player has the skill and can use it.
        """
        if self.phase != GamePhase.NIGHT:
            return False, "Not night phase"
            
        player = self.players.get(player_id)
        if not player or not player.is_alive:
            return False, "Player dead or invalid"

        # Check if role has this skill
        # Note: Witch has {SAVE, POISON}, others have 1.
        if skill_type not in player.role.skills:
            return False, "Player does not have this skill"

        # Specific checks
        if skill_type == SkillType.SAVE:
            if self.witch_save_used:
                return False, "Save potion already used"
        
        if skill_type == SkillType.POISON:
            if self.witch_poison_used:
                return False, "Poison potion already used"
                
        if skill_type == SkillType.PROTECT:
            if target_id == self.last_guarded_id:
                return False, "Cannot guard same player twice in a row"

        # Store action
        # For Wolves, they might vote. For simplicity here, last action counts.
        self.night_actions[player_id] = {
            'target_id': target_id,
            'skill_type': skill_type
        }
        return True, "Action recorded"

    def resolve_night(self):
        """
        Calculate deaths based on wolf kill, witch save/poison, guard protect.
        Handle conflicts (e.g., guard+save=die).
        """
        killed_by_wolf = None
        saved_by_witch = None
        poisoned_by_witch = None
        guarded_target = None
        
        # 1. Aggregate actions
        wolf_votes = {}
        for pid, action in self.night_actions.items():
            player = self.players[pid]
            skill = action['skill_type']
            target = action['target_id']
            
            if isinstance(player.role, Werewolf) and skill == SkillType.KILL:
                wolf_votes[target] = wolf_votes.get(target, 0) + 1
            elif isinstance(player.role, Witch):
                if skill == SkillType.SAVE:
                    saved_by_witch = target
                    self.witch_save_used = True
                elif skill == SkillType.POISON:
                    poisoned_by_witch = target
                    self.witch_poison_used = True
            elif isinstance(player.role, Guard) and skill == SkillType.PROTECT:
                guarded_target = target
                self.last_guarded_id = target

        # 2. Determine Wolf Kill Target (Majority or random if tie? Assuming consensus for now or max votes)
        if wolf_votes:
            killed_by_wolf = max(wolf_votes, key=wolf_votes.get)

        deaths = set()

        # 3. Resolve Interactions
        
        # Wolf Kill Logic
        if killed_by_wolf:
            is_dead = True
            
            # Guard protects
            if killed_by_wolf == guarded_target:
                is_dead = False
            
            # Witch saves
            if killed_by_wolf == saved_by_witch:
                if is_dead == False: 
                    # Guarded AND Saved -> Die (Conflict rule)
                    is_dead = True 
                else:
                    # Just Saved -> Live
                    is_dead = False
            
            if is_dead:
                deaths.add(killed_by_wolf)

        # Poison Logic
        if poisoned_by_witch:
            deaths.add(poisoned_by_witch)

        # Apply deaths
        for pid in deaths:
            if pid in self.players:
                player = self.players[pid]
                player.is_alive = False
                if isinstance(player.role, Hunter):
                    player.can_shoot = True
        
        self.night_deaths = deaths
        
        self.check_win()
        
        # Move to Day
        self.phase = GamePhase.DAY
        return list(deaths)

    def check_win(self) -> Optional[Team]:
        """
        Check win conditions:
        - Wolf Win: All Villagers dead OR All Gods dead (Slaughter Rule)
        - Good Win: All Wolves dead
        """
        if self.winner:
            return self.winner

        alive_wolves = [p for p in self.players.values() if p.is_alive and p.role.team == Team.WEREWOLF]
        if not alive_wolves:
            self.winner = Team.GOOD
            self.phase = GamePhase.ENDED
            return Team.GOOD

        alive_villagers = [p for p in self.players.values() if p.is_alive and isinstance(p.role, Villager)]
        alive_gods = [p for p in self.players.values() if p.is_alive and p.role.team == Team.GOOD and not isinstance(p.role, Villager)]

        if not alive_villagers or not alive_gods:
            self.winner = Team.WEREWOLF
            self.phase = GamePhase.ENDED
            return Team.WEREWOLF

        return None

    def process_day_action(self, player_id: str, target_id: str, action_type: str = "VOTE"):
        """
        Handle day actions: VOTE, SHOOT, DUEL.
        """
        if self.phase != GamePhase.DAY:
            return False, "Not day phase"

        player = self.players.get(player_id)
        if not player:
            return False, "Player not found"
            
        # Dead players can't act, unless they are Hunter shooting upon death
        if not player.is_alive and not (isinstance(player.role, Hunter) and player.can_shoot and action_type == "SHOOT"):
             return False, "Player is dead"

        if action_type == "VOTE":
            if not player.is_alive:
                return False, "Dead players cannot vote"
            if player.is_idiot_flipped:
                 return False, "Idiot cannot vote after flip"
            
            self.day_votes[player_id] = target_id
            return True, "Vote recorded"

        elif action_type == "SHOOT":
            if not isinstance(player.role, Hunter):
                return False, "Only Hunter can shoot"
            if not player.can_shoot:
                return False, "Cannot shoot now"
            
            # Execute shoot
            target = self.players.get(target_id)
            if not target or not target.is_alive:
                return False, "Invalid target"
            
            target.is_alive = False
            player.can_shoot = False # Used
            self.check_win()
            return True, f"Hunter shot {target_id}"

        elif action_type == "DUEL":
            if not isinstance(player.role, Knight):
                return False, "Only Knight can duel"
            if not player.is_alive:
                return False, "Dead Knight cannot duel"
            if SkillType.DUEL not in player.role.skills:
                 return False, "Duel skill already used" # Assuming skills are removed/marked
            
            # Remove skill to prevent reuse (if we track usage by removing from set)
            # Or we can track usage separately. Let's assume removing from set for now or add a flag.
            # But wait, Role object is shared if not careful? No, assigned per player.
            # But let's check if we want to track usage.
            # The prompt says "Handle KNIGHT_DUEL skill".
            # Let's assume single use.
            
            target = self.players.get(target_id)
            if not target or not target.is_alive:
                return False, "Invalid target"
            
            # Knight Duel Logic:
            # If target is Wolf -> Wolf dies. Knight survives.
            # If target is Good -> Knight dies. Target survives.
            
            if target.role.team == Team.WEREWOLF:
                target.is_alive = False
                msg = f"Knight duel successful! {target_id} (Wolf) died."
            else:
                player.is_alive = False
                msg = f"Knight duel failed! Knight {player_id} died."
            
            # Mark skill used
            # Here we need to make sure we don't allow reuse.
            # Let's remove DUEL from skills
            if SkillType.DUEL in player.role.skills:
                 player.role.skills.remove(SkillType.DUEL)
            
            self.check_win()
            return True, msg

        return False, "Unknown action"

    def resolve_vote(self):
        """
        Count votes, find max, execute player.
        """
        if not self.day_votes:
            return None, "No votes cast"
            
        vote_counts = Counter(self.day_votes.values())
        max_votes = max(vote_counts.values())
        candidates = [pid for pid, count in vote_counts.items() if count == max_votes]
        
        if len(candidates) > 1:
            # Tie - no death for now
            self.day_votes = {} # Reset votes
            return None, "Vote tie, no one executed"
            
        executed_id = candidates[0]
        executed_player = self.players[executed_id]
        
        # Check Idiot
        if isinstance(executed_player.role, Idiot) and not executed_player.is_idiot_flipped:
            executed_player.is_idiot_flipped = True
            self.day_votes = {}
            return executed_id, "Idiot revealed, not dead"
            
        # Execute
        executed_player.is_alive = False
        
        # Check Hunter
        if isinstance(executed_player.role, Hunter):
            executed_player.can_shoot = True
            
        self.day_votes = {}
        self.check_win()
        
        return executed_id, "Player executed"

    def next_phase(self):
        """
        Transition phase.
        Night -> Day (announce deaths) -> Night.
        """
        if self.phase == GamePhase.NIGHT:
            # Already handled in resolve_night?
            # resolve_night transitions to DAY.
            # But maybe we need a clean transition function.
            # Let's assume resolve_night is called manually or by this function.
            # For now, let's make this function just toggle or reset if needed.
            pass
        elif self.phase == GamePhase.DAY:
            self.phase = GamePhase.NIGHT
            self.round += 1
            # Reset nightly states
            self.night_actions = {}
            self.night_deaths = set()
            self.day_votes = {}
            # Reset hunter shoot permission if not used? 
            # Usually shoot must be immediate. If not used, lost.
            for p in self.players.values():
                if isinstance(p.role, Hunter):
                    p.can_shoot = False
        
        return self.phase

    def get_public_state(self):
        """
        Return info visible to everyone (alive/dead).
        """
        return {
            "phase": self.phase.value,
            "round": self.round,
            "players": {
                pid: {"is_alive": p.is_alive} 
                for pid, p in self.players.items()
            }
        }

    def get_private_state(self, player_id: str):
        """
        Return info visible to specific player (role, teammates for wolves).
        """
        if player_id not in self.players:
            return None
            
        player = self.players[player_id]
        role_info = {
            "name": player.role.name,
            "team": player.role.team.value,
            "skills": [s.value for s in player.role.skills]
        }
        
        teammates = []
        if player.role.team == Team.WEREWOLF:
            teammates = [
                pid for pid, p in self.players.items() 
                if p.role.team == Team.WEREWOLF and pid != player_id
            ]
            
        return {
            "player_id": player_id,
            "role": role_info,
            "teammates": teammates,
            "is_alive": player.is_alive
        }
