from enum import Enum
from typing import Set, Optional

class Team(Enum):
    GOOD = "GOOD"
    WEREWOLF = "WEREWOLF"

class SkillType(Enum):
    KILL = "KILL"       # 狼人杀人
    CHECK = "CHECK"     # 预言家验人
    SAVE = "SAVE"       # 女巫救人
    POISON = "POISON"   # 女巫毒人
    PROTECT = "PROTECT" # 守卫守护
    SHOOT = "SHOOT"     # 猎人开枪
    DUEL = "DUEL"       # 骑士决斗

class Role:
    def __init__(self, name: str, team: Team, skills: Optional[Set[SkillType]] = None):
        self.name = name
        self.team = team
        self.skills = skills if skills else set()

    def __repr__(self):
        return f"<Role: {self.name}>"

class Werewolf(Role):
    def __init__(self):
        super().__init__("狼人", Team.WEREWOLF, {SkillType.KILL})

class Villager(Role):
    def __init__(self):
        super().__init__("村民", Team.GOOD)

class Seer(Role):
    def __init__(self):
        super().__init__("预言家", Team.GOOD, {SkillType.CHECK})

class Witch(Role):
    def __init__(self):
        super().__init__("女巫", Team.GOOD, {SkillType.SAVE, SkillType.POISON})

class Hunter(Role):
    def __init__(self):
        super().__init__("猎人", Team.GOOD, {SkillType.SHOOT})

class Guard(Role):
    def __init__(self):
        super().__init__("守卫", Team.GOOD, {SkillType.PROTECT})

class Idiot(Role):
    def __init__(self):
        super().__init__("白痴", Team.GOOD)

class Knight(Role):
    def __init__(self):
        super().__init__("骑士", Team.GOOD, {SkillType.DUEL})
