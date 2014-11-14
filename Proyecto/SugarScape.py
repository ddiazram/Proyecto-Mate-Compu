
from matplotlib.path import Path
from random import randint, choice, randrange 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pylab

class Agent_grid(object):
    """Agent with a simple AI that inhabits a 51x51 discrete grid.
    
    Attributes
    -----------
    The agent's attributes can be divided in three sets of properties
    
    1. Intrinsic Characteristics
        id_num: Unique integer for each agent that also identifies the agent position in the list.
        sex: can be either 'M' for male and 'F' for female.
        tribe: int that represents the Agent's tribe.
        tpe: int given the Sex and the tribe, the agent is given a type number used for graphic purposes;
             it is unique for each combination of Male, Female and tribes.
        max_age: int representing the maximum age the agent can live. 
        metabolism: int between 1 and 5. Represents the rate at which the agent consumes the energy it possesses. 
                    Each step the agent takes consumes from its energy: (number of squares moved)* metabolism.
        vision: int between 1 and 2. Represents how far the agent can see in the grid. 
        
    2. Variables
        age: int representing the agents age. It starts from 1 to 10, and each step is one year.
        existence: boolean that assures the agent's existence in the world, given the fact that it can die or 
                   overlap with other agents.
        energy: int that represents the agent leftover energy.
        position: NumPy array (1x2) that represents the agent's position in that moment.
        objective: int that represents the id of the good or agent this agent wants to interact with.
        vicinity: dictionary of lists; stand for memory of the agent where it identifies it's surroundings. 
        
    3. Aux Variables    
        turn_ended: boolean; if True, the agent has already choosed to do something so he can't longer be active.         
    """
    
    def __init__(self, id_num, position=None, sex=None, tribe=None, age=None, max_age=None, 
                 metabolism=None, energy=None, vision=None):
        """Returns a new Agent_grid object."""
        self.id_num = id_num
        
        if position == None:
            self.position = np.array([randint(0,50), randint(0,50)])
        else:
            self.position = np.array(position)
            
        self.sex = sex or choice(['M','F'])
        self.tribe = tribe or randint(1, 2)
        self.age = age or randint(1,10)
        self.max_age = max_age or randint(60,100)
        self.metabolism = metabolism or randint(1,5)
        self.energy = energy or randint(10,25) 
        self.vision = vision or randint(1, 2) 
        self.existence = False
        self.objective = None
        self.turn_ended = False
        
        if self.sex == 'M':
            self.tpe = 2 * 3**self.tribe
        else:
            self.tpe = 2**2 * 3**self.tribe
            
        self.vicinity = {
            'empty_spaces': [], # arrays
            'good' : [], # arrays
            'good_id' : [], # integers
            'neighbors' : [], # arrays
            'same_tribe_id' : [], # integers
            'other_tribe_id' : [] # integers
        }
                      
    def _see(self, world , show=False):
        """Based in the vision range, the agent "sees" its vicinity in search of goods and other agents."""
        # These four if's are handle the case when the agent is in any position in the grid's border.
        if self.position[0] - self.vision < 0:
            x_min = 0
        else:
            x_min = self.position[0]-self.vision
            
        if  self.position[0] + self.vision + 1 > 51:
            x_max = 51
        else:
            x_max = self.position[0] + self.vision + 1
            
        if self.position[1] - self.vision < 0:
            y_min = 0
        else:
            y_min = self.position[1] - self.vision
            
        if self.position[1] + self.vision + 1 > 51:
            y_max = 51
        else:
            y_max = self.position[1] + self.vision + 1
        
        # Show a slice of the vicinity of the agent if True.
        if show: 
            print world.grid[x_min:x_max , y_min:y_max]
            
        return np.array([x_min, x_max, y_min, y_max])

    def _explore(self, world, agent_list):
        """Goes over the agent's action field, based in its vision range. Identifies, classifies and saves 
        in *vicinity* each type of element that is near him. 
        """
        lim = self._see(world)
        # Clean the dictionary
        for key in self.vicinity:
            self.vicinity[key] = []
            
        # Clasify things in the vicinity
        for i in xrange(lim[0], lim[1]): # Rows
            for j in xrange(lim[2], lim[3]): # Columns 
                
                if world.grid[i,j] == 0:
                    self.vicinity['empty_spaces'].append(np.array([i,j]))
                elif world.grid[i,j] == 1 or world.grid[i,j] == 2:
                    self.vicinity['good'].append(np.array([i,j]))
                elif world.grid[i,j] > 2: 
                    self.vicinity['neighbors'].append(np.array([i,j]))
                    
        # Find the goods ID of the neighbors             
        for close_good_pos in self.vicinity['good']:
            for good in world.goods_list:
                
                if np.all(close_good_pos == good.position):
                    self.vicinity['good_id'].append(good.id_num)
                    break
                    
        # Clasify the neighbors and find their ID's
        for close_neigh_pos in self.vicinity['neighbors']:
            for agent in agent_list:
                
                if np.all(close_neigh_pos == agent.position):
                    if self.tribe == agent.tribe:
                        self.vicinity['same_tribe_id'].append(agent.id_num)
                        break
                    else:
                        self.vicinity['other_tribe_id'].append(agent.id_num)
                        break
            
    def decide(self, world, agent_list): 
        """Given the fact that the agent already knows its surroundings, it chooses (after 
        some analysis) one out of for options in that order:
        1. Reproduce Sexually
        2. Reproduce Asexuall
        3. Move
        4. Trade
        """
        self._explore(world, agent_list)
        self.turn_ended = False
        if self.energy >= 75 and self.age >= 18:
            self._sex_communication(world, agent_list)
            if randint(0,1) == 1 and self.turn_ended == False:
                self._asexual_reproduction(world, agent_list)
        else:
            self._benefit_cost_analysis(world)
            self._move(world)
            
    def _benefit_cost_analysis(self, world):
        """The agent tries to maximize its yield doing a cost benefit analysis. The agent then moves to 
        the best choice availabe. If there is no best choice, it'll simply move randomly.
        
        Notes
        -----
        benefit: amount of energy units it'll recive from the good. 
        cost: amount of energy it'll consume to get to the chosen position given the agent's metabolism.
        """
        bc =  -10 #Benefit - Cost
        for i in self.vicinity['good_id']:
            a = self._benefit(world, i) - self._cost(world, i)
            if a > bc:
                bc = a
                self.objective = i
                
        if bc <= -10:
            self.objective = None
    
    def _move(self, world):
        """Agent's way of moving. There are two kinds of movement:
        1. If it does not have a desired position, it moves randomnly to an empty position.
        2. If it wants to move to an adjacent cell, it moves and consumes the good, therefore 
           removing it from existence.
        """
        if isinstance(self.objective, (int, float)):
            self.energy += (self._benefit(world, self.objective) - self._cost(world, self.objective))
            self.position = world.goods_list[self.objective].position
            world.goods_list[self.objective].existence = False #Removes the sugar from existence.
        else:
            random_choice = choice(self.vicinity['empty_spaces'])
            self.energy -= self.metabolism * self._calculate_distance(random_choice)
            self.position = random_choice
    
    def _calculate_distance(self, new_position):
        """Returns the distance between its own position and a new one with the maximun norm. 
        
        Notes
        -----
        Since the particles can move in diagonal, we're assuming a diagonal movement to be equal to one.
        """
        return max(abs(self.position - new_position)) # use broadcasting
    
    def _benefit(self, world, x):
        """The energy provided by each good."""
        return world.goods_list[x].quantity
    
    def _cost(self, world, x):
        """The cost in energy of moving."""
        return self.metabolism * self._calculate_distance(world.goods_list[x].position)
    
    def death(self, world, agent_list):
        """There are three death conditions:
        1. Each agent has a 1 in 1000 chances of dying spontaneously
        2. If an agent runs out of energy
        3. If an agent surpases it's maximum age
        """
        if randint(1,1000) == 1 or (self.energy <= 0) or (self.age > self.max_age):
            world.grid[self.position[0],self.position[1]] = 0
            self.existence = False
            new_agent = Agent_grid(id_num =len(agent_list)) #A new agent "is born" when another one dies.
            new_agent.existence == True
            agent_list.append(new_agent)
            
    def _asexual_reproduction(self, world, agent_list):
        """If there is enough energy and space the agent will try to reproduce asexually
        making an exact copy of itself.
        """
        if len(self.vicinity['empty_spaces']) > 1:
            x = len(agent_list)
            clone_position = choice(self.vicinity['empty_spaces'])
            while np.all(clone_position == self.position): 
                clone_position = choice(self.vicinity['empty_spaces'])
            agent_list.append(Agent_grid(id_num = x, position = clone_position, sex = self.sex, tribe = self.tribe, 
                                         metabolism = self.metabolism, vision = self.vision, 
                                         max_age = self.max_age,  energy = self.energy/2))
            self.energy = self.energy/2
            world.grid[agent_list[x].position[0],agent_list[x].position[1]] = agent_list[x].tpe
            agent_list[x].existence = True
            self.turn_ended = True
            
    def _sex_communication(self, world, agent_list):
        """The agent tries to comunicate with the other for further reproduction. 
        If both parties agrees, they reproduce.
        """
        if self.vicinity['same_tribe_id'] and len(self.vicinity['empty_spaces']) > 1:
            for i in self.vicinity['same_tribe_id']:
                
                if agent_list[i].sex != self.sex:
                    self.objective = i
                    self.turn_ended = True
                    break
                    
        if agent_list[self.objective].objective == self.id_num:
            self._sexual_reproduction(world, agent_list)
                                
    def _sexual_reproduction(self, world, agent_list):
        """ Sexual Reproduction where the agents have a baby and inherit some of their characteristics."""
        x = len(agent_list)
        baby_position = choice(self.vicinity['empty_spaces'])
        
        while np.all(baby_position == self.position): 
            baby_position = choice(self.vicinity['empty_spaces'])
            
        agent_list.append(Agent_grid(id_num=x, position=baby_position, tribe=self.tribe, 
                                    metabolism=choice([self.metabolism, agent_list[self.objective].metabolism]),
                                    vision=choice([self.vision, agent_list[self.objective].vision]),
                                    max_age=choice([self.max_age, agent_list[self.objective].max_age]),
                                    energy=self.energy/3 + agent_list[self.objective].energy/3))
        
        self.energy = (2*self.energy)/3
        agent_list[self.objective].energy = 2*agent_list[self.objective].energy/3
        world.grid[agent_list[x].position[0],agent_list[x].position[1]] = agent_list[x].tpe
        agent_list[x].existence = True
        self.turn_ended = True    
                    
    def state(self, world, full_state=False, see_world=False, show_existence=False, show_vicinity=False):
        """Prints the agent's information.
        
        full_state: boolean that chooses the amount of information that displays.
        """
        if full_state:
            print "Hello, I'm a type %s agent with ID: %s" % (self.tpe, self.id_num)
            print "My stats are as follows:" 
            print "\t Sex: %s" % self.sex 
            print "\t Max_age: %s" % self.max_age
            print "\t Tribe: %s" % self.tribe
            print "\t Metabolism: %s" % self.metabolism
            print "\t Vision: %s" % self.vision
            print "My current state is: "
            print "\t Age: %s" % self.age
            print "\t Energy: %s" % self.energy
            print "\t Position: %s" % self.position
        else:
            print "ID: %s" % self.id_num
            print "\t Age: %s" % self.age
            print "\t Energy: %s" % self.energy
            print "\t Position: %s" % self.position
        if show_existence:
            print "\t Existence: %s" % self.existence
        if see_world:
            print "\t Surroundings: "
            self._see(world, show = True)
        if show_vicinity:
            print "\Empty Spaces: %s" % self.vicinity['empty_spaces']
            print "\Goods Position: %s" % self.vicinity['good']
            print "\Goods ID's: %s" % self.vicinity['good_id']
            print "\Neighbors Positions: %s" % self.vicinity['neighbors']
            print "\Same Tribe ID's: %s" % self.vicinity['same_tribe_id']
            print "\Other Tribe ID's: %s" % self.vicinity['other_tribe_id']
            
class Good(object):
    """Sugar or spice on a specific location in a 51x51 grid.
    
    Attributes
    ----------
    id_num: Unique integer for each good.
    tpe: integer that represents the type of the good; 1 is sugar, and 2 is spice.
    quantity: integer that represents the ammount of units of the good. If the good
              is sugar, it's between 5 and 20; if it's spice, it's between
              5 and 15.
    position: NumPy array (1x2) that represents the good position in that moment.
    existence: boolean that assures the good's existence in the world.
    """
    def __init__(self, id_num ,tpe,  quantity = None, position = None):
        """Returns a new Good object."""
        self.id_num = id_num
        self.tpe = tpe 
        
        if self.tpe == 1:
            self.quantity = quantity or randint(5, 20) #Sugar
        else:
            self.quantity = quantity or randint(5, 15) #Spice

        if position: 
            self.position = np.array(position)
        else:
            self.position = np.array([randint(0,50), randint(0,50)])
        
        self.existence = False
        
    def __repr__(self):
        if self.tpe == 1:
            return "Sugar No.%d at [%d, %d]" % (self.id_num, self.position[0], self.position[1])
        else:
            return "Spice No.%d at [%d, %d]" % (self.id_num, self.position[0], self.position[1])
        
class World(object):
    """A SugarScape world represented by a NumPy 2D array of 51x51."""
    
    color_code = {
        1 : '#40FF00', # Sugar
        2 : '#F7FE2E', # Spice
        6 : '#FA5882', # Female, tribe 1
        12 : '#B40431', # Male, tribe 1
        18 : '#58FAD0', # Female, tribe 2
        36 : '#04B4AE', # Male, tribe 2
    } 
    
    def __init__(self):
        """Returns a new World object."""
        self.grid = np.zeros((51,51))
        self.good_list = []
        self.step = 0
    
    def place_goods(self, n, practice_goods=None):
        """Function that creates n number of goods and places them both on the grid and in the sugars_list.
        n: number of goods to be created, though you can't specify each one.
        practice_goods: list that contains handcrafted goods in specific locations for trials purposes.
        """
        if practice_goods:
            self.goods_list = practice_goods
            self.define(self.goods_list)
        else:
            self.goods_list = [Good(i) for i in xrange(n)]
            self.define(self.goods_list)   
                            
    def define(self, thing_list):
        """Gives the things existence in the world. This means that this method places each agent in the grid (2D NumPy array),
        accordingly to its random location given by its attribute self.position
        
        When it is placed, we say that the agent "exists" in the world. 
        
        If that cell is already taken, it looks for a new random location for the agent to exist until it finds an empty cell.
        """
        for thing in thing_list:
            while thing.existence == False:
                if self.grid[thing.position[0], thing.position[1]] == 0:
                    self.grid[thing.position[0], thing.position[1]] = thing.tpe # bien pensado
                    thing.existence = True
                else:
                    thing.position = np.array([randint(0,50), randint(0,50)])
                 
    def update_agents(self, agent_list):
        """The basic function for animating the world. It can't be done with the quick method because 
        the new agents would move too.
        """
        n = len(agent_list)
        for i in xrange(n):
            agent_list[i].death(self, agent_list)
            if agent_list[i].existence == True:
                self.grid[agent_list[i].position[0], agent_list[i].position[1]] = 0
                agent_list[i].decide(self, agent_list)
                self.grid[agent_list[i].position[0], agent_list[i].position[1]] = agent_list[i].tpe
                agent_list[i].age += 1
        self.step += 1        
            
    def _count_agents(self, agent_list):
        count = 0
        for agent in agent_list:
            if agent.existence == True:
                count += 1
        return count
    
    def update_goods(self, agent_list):
        """Since the world is finite and the goods get consumed each step, there needs to exist a 
        method of good regeneration.
        
        There are two methods:
        1. If the good population goes down to one fifth of the original, all the sugars get placed again
        2. Each step, some random goods, if they meet the requirements, they get regenerated
        """
        if self._count_agents(self.goods_list) <= len(self.goods_list)/5: #One fifth?
            self.define(self.goods_list)
            
        for i in xrange(len(agent_list)/3): #Third?
            lucky_good = randint(0,len(self.goods_list)-1)
            if (self.goods_list[lucky_good].existence == False and 
                self.grid[self.goods_list[lucky_good].position[0],self.goods_list[lucky_good].position[1]] == 0):
                    self.grid[self.goods_list[lucky_good].position[0],self.goods_list[lucky_good].position[1]] = self.goods_list[lucky_good].tpe 
                    self.goods_list[lucky_good].existence = True
                  
    def lorenz(self, agent_list):
        """Calculates the points of a Lorenz Curve."""
        energy_incomes = []
        for agent in agent_list:
            if agent.existence == True:
                energy_incomes.append(agent.energy)
        n = len(energy_incomes)
        c = sort(energy_incomes)
        c = cumsum(c)
        c = np.insert(c,[0],0)
        points = np.zeros([n+1,2])
        for i in xrange(n+1):
            points[i,0] = 100*(i+0.0)/n
            points[i,1] = 100*(c[i]+0.0)/c[n]
        return points
    
    def gini(self, agent_list, plot = False):
        """Calculaes the Gini Coeficient x 100.
        
        The Gini Coeficient calculates the inequalities of a society.
        1 being the perfect inequality
        0 being the perfect equality
        """
        points = self.lorenz(agent_list)
        n = len(points[:,1])-1
        gini = (100 + (100 - 2*sum(points[:,1]))/(n + 0.0))
        if plot == False:
            return gini
        else:
            plt.figure(figsize(10,10), dpi = 80);
            grid(True, color = 'b' ,  linestyle = '-', linewidth = .3);
            plt.xlim = (0,100)
            plt.ylim = (0,100)
            plt.plot([0,100],[0,100], color = "orange", lw=4) #Perfect Equality
            plt.plot([0,100],[0,0], color = "red", lw=5) #Perfect Inequality
            plt.plot([100,100],[0,100], color = "red", lw=5) #Perfect Inequality
            plt.plot(points[:,0], points[:,1], label = r"Lorenz Curve", color = "blue", lw = 2 )
            # plt.title('Lorenz Curve and Gini Coefficicient',fontsize=20)
            plt.legend(loc='upper left', fontsize = 18 , frameon = False);
            plt.text(10.6, 90, r' Gini $=$ $%s$' % gini , fontsize = 19)
            plt.ylabel("% of Population", fontsize = 'xx-large');
            plt.xlabel("% of Income", fontsize = 'xx-large');
            plt.show()
    
    def state(self, agent_list, agent_state=False):
        """Function that reviews the world in its current state.
        """
        print "Step: %s" % self.step
        print "Number of Agents: %s" % self._count_agents(agent_list)
        print "Number of Goods: %s" % self._count_agents(self.goods_list)
        print "Gini: %s" % self.gini(agent_list)
        if agent_state == True:
            for agent in agent_list:
                agent.state(self)
    
    def draw(self):
        dibujar.draw_matrix(self.grid,  self.color_code)        