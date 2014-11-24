
import numpy as np
import matplotlib.pyplot as plt
from random import randint, choice

class Agent_grid:
    """Agent with a specific location in a 51x51 discrete grid.
        id: saves a unique number for each agent
        tpe: number for graphic purposes. It is unique for each combination of Male, Female and tribes.
        sex: Male of Female
        tribe: Int that represents the Agents tribe.
        age: int representing the agents age. It starts from 1 to 10
        max_age: int representing the maximum age the agent can live. 
        existence: boolean type attribute that assures the agent's existence in the world, given the fact that it can
                  die or overlap with other agents.
        turn_ended: boolean. If True, the agent has already choosed to do something so he can't longer be active          
        position: np.array (1x2) that represents the agent's position in that moment.
        vision: int attribute between 1 and 2, intrinsic characteristic of each agent that allows it to have greater 
                action field.
        objective: determines if the agent is moving to a specific targeted position.
        vicinity: dictionary in which agents, sugars and other items surrounding an agent are stored.
        metabolism: represents the rate at which the agent consumes the energy it possesses. 
        energy: number which helps the agent decide where to move, due to the fact that the agent can die if its energy runs out.
    """
    
    def __init__(self, id ,tpe = 2, position = None, sex = None, age = None, max_age = None, 
                 metabolism = None, energy = None, vision = None, tribe = None):
        self.id = id
        self.existence = False
        self.turn_ended = False
        #Tribe
        if tribe == None:
            self.tribe = randint(1,2)
        else:
            self.tribe = tribe
        #Sex
        if sex == None:
            self.sex = choice(['M','F'])
        else:
            self.sex = sex
        #Type
        if self.sex == 'M':
            self.tpe = 2*(3**self.tribe)
        else:
            self.tpe = (2**2)*(3**self.tribe)
        #Age
        if age == None:
            self.age = randint(1,10)
        else:
            self.age = age
        #Max_age
        if max_age == None:
            self.max_age = randint(60,100)
        else:
            self.max_age = max_age
        #Metabolism    
        if metabolism == None:
            self.metabolism = randint(1,5)
        else:
            self.metabolism = metabolism
        #Energy    
        if energy == None:
            self.energy = randint(10,25)
        else:
            self.energy = energy
        #Vision    
        if vision == None:
            self.vision = randint(1,2)
        else:
            self.vision = vision    
        #Position
        if position == None:
            self.position = np.array([randint(0,50), randint(0,50)])
        else:
            self.position = np.array(position)
        self.objective = None
        #Dictionary to store information about the things nearby
        self.vicinity= {'empty_spaces': [],
                        'sugar' : [], 
                        'sugar_id' : [],
                        'neighbors' : [],        #Positions.
                        'same_tribe_id' : [],
                        'other_tribe_id' : []}
                      
    def see(self, world , show = False):
        """
        Based in the vision range, the agent "sees" its vicinity in search of sugar and other agents.
        The four if's are implemented when the agent is in any position in the grid's border. In this way we avoid that it gets
        out of the array.
        """
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
            y_max =self.position[1] + self.vision + 1
        if show == True: #This condition shows us a slice of the vicinity of the agent if the condition is True
            print world.grid[x_min : x_max , y_min : y_max]  
        return np.array([x_min,x_max,y_min,y_max])

    def explore(self, world, agent_list):
        """
        Goes over the agant's action field, based in its vision range. 
        Identifies and saves in a dictionary each type of element that is near the agent so then the agent can take a decision.
        Due to the fact that the vicinity changes after each iteration (each time the agent moves), in each step we clean
        vicinity dictionary.
        """
        lim = self.see(world)
        self.vicinity['empty_spaces'] = []
        self.vicinity['sugar'] = []
        self.vicinity['sugar_id'] = []
        self.vicinity['neighbors'] = []
        self.vicinity['same_tribe_id'] = [],
        self.vicinity['other_tribe_id'] = []
        #Clasify the whole vicinity
        for i in xrange(lim[0],lim[1]): #Rows
            for j in xrange(lim[2],lim[3]): #Columns 
                if world.grid[i,j] == 0:
                    self.vicinity['empty_spaces'].append(np.array([i,j]))
                elif world.grid[i,j] == 1:
                    self.vicinity['sugar'].append(np.array([i,j]))
                elif world.grid[i,j] > 2: 
                    self.vicinity['neighbors'].append(np.array([i,j]))
        #Find the sugars ID of the neighbors             
        for close_sugar_pos in self.vicinity['sugar']:
            for sugar in world.sugars_list:
                if np.all(close_sugar_pos == sugar.position):
                    self.vicinity['sugar_id'].append(sugar.id)
                    break
        #Clasify the neighbors and find their Id's
        for close_neigh_pos in self.vicinity['neigbors']:
            for agent in agent_list:
                if np.all(close_neigh_pos == agent.position):
                    if self.tribe == agent.tribe:
                        self.vicinity['same_tribe_id'].append(agent.id)
                        break
                    else:
                        self.vicinity['other_tribe_id'].append(agent.id)
                        break
            
    def decide(self, world, agent_list): 
        """
        Given the fact that the agent already knows its surroundings, it chooses one out of for options:
        1. Move
        2. Reproduce Asexually
        3. Reproduce Sexually
        4. Trade
        """
        self.explore(world, agent_list)
        self.turn_ended = False
        if randint(0,1) == 1:
            self.asexual_reporoduction(world, agent_list)
        if self.turn_ended == False:
            self.benefit_cost_analysis(world)
            self.move(world)
            
    def benefit_cost_analysis(self, world):
        """
        The agent tries to maximize its yield doing a cost benefit analysis.
        The agent then moves to the best choice availabe. If there is no best choice, it'll simply move randomly.
        benefit = amount of energy units it'll recive from the sugar. Each sugar gives 1 energy unit.
        cost = amount of energy it'll consume to get to the chosen position given the agent's metabolism.
        """
        bc =  -10 #Benefit - Cost
        for i in self.vicinity['sugar_id']:
            if self.benefit(world, i) - self.cost(world, i) > bc:
                bc = self.benefit(world, i) - self.cost(world, i)
                self.objective = i
        if bc <= -10:
            self.objective = None
    
    def move(self, world):
        """
        Agent's way of moving.
        Two kinds of movement:
        1. If they do not have a desired position, they move randomnly to an empty position.
        2. If they want to move to an adjacent cell, it moves and consumes the sugar, therefore removing it from existence
        """
        if self.objective == None:
            random_choice = choice(self.vicinity['empty_spaces'])
            self.energy -= self.metabolism * self.calculate_distance(random_choice)
            self.position = random_choice
        else:
            self.energy += self.benefit(world, self.objective)  - self.cost(world, self.objective)
            self.position = world.sugars_list[self.objective].position
            world.sugars_list[self.objective].existence = False #Removes the sugar from existence.
    
    def calculate_distance(self, new_position):
        """
        Caculates the distance between its own position and a new one with the maximun norm (A square). 
        Since the particles can move in diagonal, we're assuming a diagonal movement to be equal to one.
        """
        return max(abs(self.position - new_position))
    
    def benefit(self, world, x):
        """
        The energy provided by each sugar
        """
        return world.sugars_list[x].quantity
    
    def cost(self, world, x):
        """
        The cost in energy of moving
        """
        return self.metabolism * self.calculate_distance(world.sugars_list[x].position)
    
    def death(self, world):
        """
        Three death conditions:
        1. Each agent has a 1 in 1000 chances of dying spontaneously
        2. If an agent runs out of enery
        3. If an agent surpases it's maximum age
        
        The agent removes itself from existence, both theoricaly and on the world.
        """
        if 1 == randint(1,1000) or self.energy <= 0 or self.age > self.max_age:
            world.grid[self.position[0],self.position[1]] = 0
            self.existence = False
            
    def asexual_reporoduction(self, world, agent_list):
        if self.energy >= 75 and len(self.vicinity['empty_spaces']) > 1: #75?
            x = len(agent_list)
            clone_position = choice(self.vicinity['empty_spaces'])
            while np.all(clone_position == self.position): 
                clone_position = choice(self.vicinity['empty_spaces'])
            agent_list.append(Agent_grid(id = x, tpe = self.tpe, position = clone_position,
                                         metabolism = self.metabolism, vision = self.vision, max_age = self.max_age,
                                         energy = self.energy/2))
            self.energy = self.energy/2
            world.grid[agent_list[x].position[0],agent_list[x].position[1]] = agent_list[x].tpe
            agent_list[x].existence = True
            self.turn_ended = True
            
            
    def state(self, world, full_state = False, see_world = False, show_existence = False):
        """
        Handy function to review an specific agent and its caracteristics
        full_state: boolean that chooses the amount of information that displays.
        """
        if full_state == True:
            print "Hello, I'm a type %s agent with ID: %s" % (self.tpe, self.id)
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
            print "\t Age: %s" % self.age
            print "\t Energy: %s" % self.energy
            print "\t Position: %s" % self.position
        if see_world == True:
            print "\t Surroundings: "
            self.see(show = True)
        if show_existence == True:
            print "\t Existence: %s" % self.existence

class Sugar:
    """
    Stacks of sugar of variable sizes in a specific location in a discrete grid.
    """
    
    def __init__(self, id ,tpe = 1, x = None, y = None, quantity = None):
        self.id = id
        self.tpe = tpe #type
        self.existence = False
        #Position
        if x == None or y == None:
            self.position = np.array([randint(0,50), randint(0,50)])
        else:
            self.position = np.array([x,y])
        #Quantity
        if quantity == None:
            self.quantity = randint(5,20)
        else: 
            self.quantity = quantity

class World:
    """
    A SugarScape world represented by a NumPy 2D array of 51x51. ie:
    grid = NumPy 2D 51x51 array 
    """
    
    def __init__(self):
        """We create a zero's grid"""
        self.grid = np.zeros((51,51))
        self.sugars_list = []
        self.step = 0
    
    def place_sugars(self, n, practice_sugars = None):
        """
        Function that creates n number of sugars and places them both on the grid and in the sugars_list.
        n: number of sugars to be created, though you can't specify each one.
        practice_sugars: list that contains handcrafted sugars in specific locations for trials purposes.
        """
        if practice_sugars == None:
            self.sugars_list = [Sugar(i) for i in xrange(n)]
            self.define(self.sugars_list)       
        else:
            self.sugars_list = practice_sugars
            self.define(self.sugars_list)
                            
    
    def define(self, agent_list, agent_id = None):
        """
        Gives the agents existence in the world. This means that this method places each agent in the grid (2D NumPy array),
        accordingly to its random location given by its attribute self.position
        When it is placed, we say that the agent "exists" in the world. 
        If that cell is already taken, it looks for a new random location for the agent to exist until it finds an empty cell.
        """
        for agent in agent_list:
            while agent.existence == False:
                if self.grid[agent.position[0],agent.position[1]] == 0:
                    self.grid[agent.position[0],agent.position[1]] = agent.tpe
                    agent.existence = True
                else:
                    agent.position = np.array([randint(0,50), randint(0,50)])
                 
    def update_agents(self, agent_list):
        """
        The basic function for animating the world. It can't be done with the quick method because the new agents would move too
        """
        n = len(agent_list)
        for i in xrange(n):
            agent_list[i].death(self)
            if agent_list[i].existence == True:
                self.grid[agent_list[i].position[0], agent_list[i].position[1]] = 0
                agent_list[i].decide(self, agent_list)
                self.grid[agent_list[i].position[0], agent_list[i].position[1]] = agent_list[i].tpe
                agent_list[i].age += 1
        self.step += 1        
            
    def count_agents(self, agent_list):
        count = 0
        for agent in agent_list:
            if agent.existence == True:
                count += 1
        return count
    
   
    def update_sugars(self, agent_list):
        """
        Since the world is finite and the sugars get consumed each step, there needs to exist a method of sugar regeneration.
        There are two methods:
        1. If the sugar population goes down to one fifth of the original, all the sugars get placed again
        2. Each step, some random sugars, if they meet the requirements, they get regenerated
        """
        if self.count_agents(self.sugars_list) <= len(self.sugars_list)/5: #One fifth?
            self.define(self.sugars_list)
        for i in xrange(len(agent_list)/3): #Third?
            lucky_sugar = randint(0,len(self.sugars_list))
            if (self.sugars_list[lucky_sugar].existence == False and 
                self.grid[self.sugars_list[lucky_sugar].position[0],self.sugars_list[lucky_sugar].position[1]] == 0):
                    self.grid[self.sugars_list[lucky_sugar].position[0],self.sugars_list[lucky_sugar].position[1]] = 1 
                    self.sugars_list[lucky_sugar].existence = True
            
            
    def lorenz(self, agent_list):
        """
        Calculates the points of a Lorenz Curve
        """
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
        """
        Calculaes the Gini Coeficient x 100.
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
    
    def state(self, agent_list):
        """
        Function that reviews the world in its current state
        """
        print "Step: %s" % self.step
        print "Number of Agents: %s" % self.count_agents(agent_list)
        print "Number of Sugars: %s" % self.count_agents(self.sugars_list)
        print "Gini: %s" % self.gini(agent_list)
    
    def draw(self):
        plt.figure(figsize=(11,10), dpi=80)
        pyplot.pcolor(-numpy.flipud(self.grid))
        plt.axis([0, 51, 0, 51])
#         plt.gray()
#         plt.colorbar() #ELIMINAR es para fines de pruebas
#         plt.axis('off') #ELIMINAR
        plt.show()            
            