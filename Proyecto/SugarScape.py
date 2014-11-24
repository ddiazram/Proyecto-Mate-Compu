
class Agent_grid:
    """Agent with a specific location in a 51x51 discrete grid.
        id: saves a unique number for each agent
        tpe: number for graphic purposes.
        sex: Male of Female
        age: int representing the agents age. It starts from 1 to 10
        max_age: int representing the maximum age the agent can live. 
        existence: boolean type attribute that assures the agent's existence in the world, given the fact that it can
                  die or overlap with other agents.
        position: np.array (1x2) that represents the agent's position in that moment.
        vision: int attribute between 1 and 2, intrinsic characteristic of each agent that allows it to have greater 
                action field.
        objective: determines if the agent is moving to a specific targeted position.
        vicinity: dictionary in which agents, sugars and other items surrounding an agent are stored.
        metabolism: represents the rate at which the agent consumes the energy it possesses. 
        energy: number which helps the agent decide where to move, due to the fact that the agent can die if its energy runs out.
    """
    
    def __init__(self, id ,tpe = 2, x = None, y = None, sex = None, age = None, max_age = None, 
                 metabolism = None, energy = None, vision = None):
        self.id = id
        self.tpe = tpe #type
        self.existence = False
        #Sex
        if sex == None:
            self.sex = choice(['M','F'])
        else:
            self.sex = sex
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
            self.energy = randint(10,20)
        else:
            self.energy = energy
        #Vision    
        if vision == None:
            self.vision = randint(1,2)
        else:
            self.vision = vision    
        #Position
        if x == None or y == None:
            self.position = np.array([randint(0,50), randint(0,50)])
        else:
            self.position = np.array([x,y])
            
        self.objective = None
        #Dictionary to store information about the things nearby
        self.vicinity= {'sugar' : [], 
                         'sugar_id' : [],
                         'neighbors' : [],
                         'empty_spaces': []}
                      
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

    def explore(self, world):
        """
        Goes over the agant's action field, based in its vision range. 
        Identifies and saves in a dictionary each type of element that is near the agent so then the agent can take a decision.
        Due to the fact that the vicinity changes after each iteration (each time the agent moves), in each step we clean
        vicinity dictionary.
        """
        lim = self.see(world)
        self.vicinity['neighbors'] = []
        self.vicinity['sugar'] = []
        self.vicinity['sugar_id'] = []
        self.vicinity['empty_spaces'] = []
        #Clasify the whole vicinity
        for i in xrange(lim[0],lim[1]): #Rows
            for j in xrange(lim[2],lim[3]): #Columns 
                if world.grid[i,j] == 0:
                    self.vicinity['empty_spaces'].append(np.array([i,j]))
                elif world.grid[i,j] == 1:
                    self.vicinity['sugar'].append(np.array([i,j]))
                elif world.grid[i,j] == 2: 
                    self.vicinity['neighbors'].append(np.array([i,j]))
        #Find the sugars ID of the neighbors             
        for close_sugar_pos in self.vicinity['sugar']:
            for sugar in world.sugars_list:
                if np.all(close_sugar_pos == sugar.position):
                    self.vicinity['sugar_id'].append(sugar.id)
                    break
                
    def decide(self, world): 
        """
        Given the fact that the agent already knows its surroundings, it tries to maximize its yield doing a cost benefit analysis.
        The agent then moves to the best choice availabe. If there is no best choice, it'll simply move randomly.
        benefit = amount of energy units it'll recive from the sugar. Each sugar gives 1 energy unit.
        cost = amount of energy it'll consume to get to the chosen position given the agent's metabolism.
        """
        self.explore(world)
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
        2. If they want to move to an adjacent cell, it moves and consumes the sugar, therefore removing it from existance
        """
        self.decide(world) 
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
        
        The agent removes itself from existance, both theoricaly and on the world.
        """
        if 1 == randint(1,1000) or self.energy <= 0 or self.age > self.max_age:
            self.existence = False
            world.grid[self.position[0],self.position[1]] = 0
            
    def state(self, world, full_state = False, see_world = False):
        """
        Handy function to review an specific agent and its caracteristics
        full_state: boolean that chooses the amount of information that displays.
        """
        if full_state == True:
            print "Hello, I'm a type %s agent with ID: %s" % (self.tpe, self.id)
            print "My stats are as follows:" 
            print "\t Sex: %s" % self.sex 
            print "\t Max_age_ %s" % self.max_age
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
                            
    
    def define(self, agent_list):
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
            
    def update_agents(self, agent_list, step):
        for agent in agent_list:
            agent.death(self)
            if agent.existence == True:
                self.grid[agent.position[0], agent.position[1]] = 0
                agent.move(self)
                self.grid[agent.position[0], agent.position[1]] = agent.tpe
                agent.age += 1
        self.step += 1        
            
    def count_agents(self, agent_list):
        count = 0
        for agent in agent_list:
            if agent.existence == True:
                count += 1
        return count
    
   
    def update_sugars(self):
        if self.count_agents(self.sugars_list) <= 50:
            self.define(self.sugars_list)
            
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
        n = len(points[0,:])-1
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
        plt.gray()
        plt.colorbar() #ELIMINAR es para fines de pruebas
#         plt.axis('off') #ELIMINAR
        plt.show()