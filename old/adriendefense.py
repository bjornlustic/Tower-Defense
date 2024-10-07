class Towers:
  def __init__(self, health, damage, firerate, range, abilities, cost, buffs, name):
    self.health = health
    self.damage = damage
    self.firerate = firerate
    self.range = range
    self.abilities = abilities
    self.cost = cost
    self.buffs = buffs
    self.name = name
    
recon = Towers(65, 1, 1.2, 12, "none", 350, "none", "recon")
sniper = Towers(80, 8, 2.4, 18, "none", 500, "none", "sniper")
shotgunner = Towers(75, 2, 1.6, 8, "spread", 700, "none", "shotgunner")
pyro = Towers(50, 1, 0.5, 6, "fire", 1200, "none", "pyro")  
cultist = Towers(80, 0, 0, 14, "cult", 1675, "cult", "cultist")


class Enemies:
  def __init__(self, health, walkspeed, damage, range, abilites, traits, name):
    self.health = health
    self.walkspeed = walkspeed
    self.damage = damage
    self.range = range
    self.abilites = abilites
    self.traits = traits
    self.name = name
    
normie = Enemies(4, 1.2, 0, 0, "none", "none", "normie")
speedy = Enemies(5, 3, 0, 0, "none", "none", "speedy")
tough = Enemies(16, 0, 0, 0, "none", "traits", "tough" )


print(sniper.cost)
print(sniper.damage)
print(recon.range)
print(normie.traits)
print(normie)