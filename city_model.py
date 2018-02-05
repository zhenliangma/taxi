#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 13:00:15 2017

@author: bokanyie
"""

import numpy as np
from random import shuffle,choice
import matplotlib.pyplot as plt
from queue import Queue
import pdb
import pickle

class City():
    """
    Represents a grid on which taxis are moving.
    """

    def __init__(self,**config):
        """      
        Parameters
        ----------
        
        n : int
            width of grid
        
        m : int
            height of grid

        base_coords : [int,int]
            grid coordinates of the taxi base
            
        base_sigma : float
            standard deviation of the 2D Gauss distribution
            around the taxi base

        Attributes
        ----------
        A : np.array of lists
            placeholder to store list of available taxi_ids at their actual
            positions

        n : int
            width of grid
        
        m : int
            height of grid

        base_coords: [int,int]
            coordinates of the taxi base
            
        base_sigma: float
            standard deviation of the 2D Gauss distribution
            around the taxi base
                    
        
        
        """
        if (("n" in config) and ("m" in config)):
            self.n = config["n"] # number of pixels in x direction
            self.m = config["m"] # number of pixels in y direction

            # array that stores taxi_id of available taxis at the
            # specific position on the grid
            # we initialize this array with empy lists
            self.A = np.empty((self.n,self.m),dtype=list)
            for i in range(self.n):
                for j in range(self.m):
                    self.A[i,j]=list()
                    
            self.base_coords = [int(np.floor(self.n/2)-1),int(np.floor(self.m/2)-1)]
#            print(self.base_coords)
            self.base_sigma = config["base_sigma"]

    def measure_distance(self,source,destination):
        """
        Measure distance on the grid between two points.
        
        Returns
        -------
        Source coordinates are marked by *s*,
        destination coordinates are marked by *d*.
        
        The distance is the following integer:
        $$|x_s-x_d|+|y_s-y_d|$$
        """

        return np.dot(np.abs(np.array(destination)-np.array(source)),[1,1])

    def create_path(self,source,destination):
        """
        Choose a random shortest path between source and destination.
        
        Parameters
        ----------
        
        source : [int,int]
            grid coordinates of the source
            
        destination : [int,int]
            grid coordinates of the destination
        
        
        Returns
        -------
        
        path : list of coordinate tuples
            coordinate list of a random path between source and destinaton
            
        """
        
        # distance along the x and the y axis
        dx, dy = np.array(destination) - np.array(source)
        # create a sequence of "x"-es and "y"-s
        # we are going to shuffle this sequence
        # to get a random order of "x" and "y" direction steps
        sequence = ['x']*int(np.abs(dx))+['y']*int(np.abs(dy))
        shuffle(sequence)
        # source is included in the path
        path=[source]
        for item in sequence:
            if item=="x":
                # we add one step in the "x" direction based on the last position
                path.append([np.sign(dx)+path[-1][0],0+path[-1][1]])
            else:
                # we add one step in the "y" direction based on the last position
                path.append([0+path[-1][0],np.sign(dy)+path[-1][1]])
        return path

    def neighbors(self,coordinates):
        """
        Calculate the neighbors of a coordinate.
        On the edges of the simulation grid, there are no neighbors.
        (E.g. there are only 2 neighbors in the corners.)

        Parameters
        ----------
        
        coordinates : [int,int]
            input grid coordinate
            
        Returns
        -------
        
        ns : list of coordinate tuples
            list containing the coordinates of the neighbors        
        """

        ns = set()
        for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
            new_x = coordinates[0]+dx
            new_y = coordinates[1]+dy

            if ((0<=new_x) and (self.n>new_x) and (0<=new_y) and (self.m>new_y)):
                ns.add((new_x,new_y))
        return ns
    
    def create_request_coords(self, mean=None):
        """
        Creates random request coords based on the base_coords and the
        base_sigma according to a 2D Gauss.
        
        Returns
        -------
        
        x,y
            coordinate tuple
        """
        
        done=False
        while(not done):
            if mean is None:
                mean = self.base_coords
            cov = np.array([[self.base_sigma**2,0],[0,self.base_sigma**2]])
            
            x,y=np.random.multivariate_normal(mean,cov)
            
            x = int(np.floor(x))
            y = int(np.floor(y))
            
            if ((x>=0) and (x<self.n) and (y>=0) and (y<self.m)):
                done=True
        return x,y

class Taxi():
    """
    Represents a taxi in the simulation.
    
    Attributes
    ----------
    
    x : int
        horizontal grid coordinate
    
    y : int
        vertical grid coordinate
    
    taxi_id : int
        unique identifier of taxi
        
    available : bool
        flag that stores whether taxi is free
        
    to_request : bool
        flag that stores when taxi is moving towards a request
        but there is still no user sitting in it
    
    with_passenger : bool
        flag that stores when taxi is carrying a passenger
        
    actual_request_executing : int
        id of request that is being executed by the taxi
        
    requests_completed : list of ints
        list of requests completed by taxi
        
    waiting_time : int
        time spent with empty waiting
    
    useful_travel_time : int
        time spent with carrying a passenger
        
    empty_travel_time : int
        time spent with travelling to a request
        
    next_destination : Queue
        Queue that stores the path forward of the taxi
    
    """
    def __init__(self,coords = None,taxi_id = None):
        if coords == None:
            print("You have to put your taxi somewhere in the city!")
        elif taxi_id == None:
            print("Not a licenced taxi.")
        else:
            
            self.x=coords[0]
            self.y=coords[1]
            
            self.taxi_id=taxi_id
            
            self.available=True
            self.to_request=False
            self.with_passenger=False
            
            self.actual_request_executing=None
            self.requests_completed=[]
                        
            # metrics
            self.waiting_time=0
            self.useful_travel_time=0
            self.empty_travel_time=0

            # storing steps to take
            self.next_destination=Queue() # path to travel
            
    def __str__(self):
        s = [
                "Taxi ",
                str(self.taxi_id),
                ".\n\tPosition ",
                str(self.x)+","+str(self.y)+"\n"
                ]
        if self.available:
            s+=["\tAvailable.\n"]
        elif self.to_request:
            s+=["\tTravelling towards request "+str(self.actual_request_executing)+".\n"]
        elif self.with_passenger:
            s+=["\tCarrying the passenger of request "+str(self.actual_request_executing)+".\n"]

        return "".join(s)

class Request():
    """
    Represents a request that is being made.
    
    Attributes
    ----------
    
    ox,oy : int
        grid coordinates of request origin
        
    dx,dy : int
        grid coordinates of request destination
        
    request_id : int
        unique id of request
    
    request_timestamp : int
        timestamp of request
        
    pickup_timestamp : int
        timestamp of taxi arrival
        
    dropoff_timestamp : int
        timestamp of request completed
    
    taxi_id : int
        id of taxi that serves the request
    
    waiting_time : int
        how much time the user had to wait until picked up
    """

    def __init__(self,ocoords = None, dcoords=None, request_id = None, timestamp = None):
        """
        
        """
        if (ocoords == None) or (dcoords==None):
            print("A request has to have a well-defined origin and destination.")
        elif request_id == None:
            print("Please indentify each request uniquely.")
        elif timestamp == None:
            print("Please give a timestamp for the request!")
        else:
            # pickup coordinates
            self.ox = ocoords[0]
            self.oy = ocoords[1]
            
            # desired dropoff coordinates
            self.dx = dcoords[0]
            self.dy = dcoords[1]

            self.request_id = request_id

            self.request_timestamp = timestamp
            
            # travel data
            self.pickup_timestamp = None
            self.dropoff_timestamp = None
            self.taxi_id=None

            self.waiting_time=0
            
    def __str__(self):
        s = [
            "Request ",
            str(self.request_id),
            ".\n\tOrigin ",
            str(self.ox)+","+str(self.oy)+"\n",
            "\tDestination ",
            str(self.dx)+","+str(self.dy)+"\n"
        ]
        if self.taxi_id!=None:
            s+=["\tTaxi assigned ",str(self.taxi_id),".\n"]
        else:
            s+=["\tWaiting."]

        return "".join(s) 
            

class Simulation():
    """
    Class for containing the elements of the simulation.
    
    Attributes
    ----------
    time : int
        stores the time elapsed in the simulation
    
    num_taxis : int
        how many taxis there are
    
    request_rate : float
        rate of requests per time period
    
    hard_limit : int
        max distance from which a taxi is still assigned to a request
    
    taxis : dict
        storing all Taxi() instances in a dict
        keys are `taxi_id`s
    
    latest_taxi_id : int
        shows latest given taxi_id
        used or generating new taxis
    
    taxis_available : list of int
        stores `taxi_id`s of available taxis
    
    taxis_to_request : list of int
        stores `taxi_id`s of taxis moving to serve a request
    
    taxis_to_destination : list of int
        stores `taxi_id`s of taxis with passenger
    
    requests : dict
        storing all Request() instances in a dict
        keys are `request_id`s
    
    latest_request_id : int
        shows latest given request_id
        used or generating new requests
    
    requests_pending : list of int
        requests waiting to be served
    
    requests_in_progress : list of int
        requests with assigned taxis
    
    requests_fulfilled : list of int
        requests that are closed
    
    requests_dropped : list of int
        unsuccessful requests
    
    city : City
        geometry of class City() underlying the simulation
        
    show_map_labels : bool
    
    """

    def __init__(self,**config):
        
        # initializing empty grid
        self.time = 0
        

        self.num_taxis = config["num_taxis"]
        self.request_rate = config["request_rate"]
        self.hard_limit = config["hard_limit"]
        
        if "price_fixed" in config:
            self.price_fixed = config["price_fixed"]
        else:
            self.price_fixed = 0
        if "price_per_dist" in config:
            self.price_per_dist = config["price_per_dist"]
        else:
            self.price_per_dist = 1

        self.taxis={}
        self.latest_taxi_id = 0
        
        self.taxis_available=[]
        self.taxis_to_request=[]
        self.taxis_to_destination=[]

        self.requests={}
        self.latest_request_id = 0
        
        self.requests_pending=[]
        self.requests_in_progress=[]
        self.requests_fulfilled=[]
        self.requests_dropped=[]

        self.city = City(**config)
        
        self.log = config["log"]
        self.show_plot = config["show_plot"]

        # initializing simulation with taxis
        for t in range(self.num_taxis):
            self.add_taxi(t)

        if self.show_plot:
    #         plotting variables
            self.canvas = plt.figure()
            self.canvas_ax = self.canvas.add_subplot(1,1,1)
            self.canvas_ax.set_aspect('equal', 'box')
            self.cmap = plt.get_cmap('viridis')
            self.taxi_colors = np.linspace(0,1,self.num_taxis)
            self.show_map_labels=config["show_map_labels"]
            self.show_pending=config["show_pending"]
            self.init_canvas()

    def init_canvas(self):
        """
        Initialize plot.
        
        """
        self.canvas_ax.clear()
        self.canvas_ax.set_xlim(-0.5,self.city.n-0.5)
        self.canvas_ax.set_ylim(-0.5,self.city.m-0.5)

        self.canvas_ax.tick_params(length=0)
        self.canvas_ax.xaxis.set_ticks(list(range(self.city.n)))
        self.canvas_ax.yaxis.set_ticks(list(range(self.city.m)))
        if not self.show_map_labels:
            self.canvas_ax.xaxis.set_ticklabels([])
            self.canvas_ax.yaxis.set_ticklabels([])
        
        self.canvas_ax.set_aspect('equal', 'box')
        self.canvas.tight_layout()
        self.canvas_ax.grid()

    def add_taxi(self,taxi_id):
        """
        Create new taxi.
        
        """
        # create a taxi at the base
        tx = Taxi(self.city.base_coords,self.latest_taxi_id)
        
        # add to taxi storage
        self.taxis[self.latest_taxi_id]= tx
        # add to available taxi storage
        self.city.A[self.city.base_coords[0],self.city.base_coords[1]].append(self.latest_taxi_id) # add to available taxi matrix
        self.taxis_available.append(self.latest_taxi_id)
        
        # increase id
        self.latest_taxi_id+=1

    def add_request(self,request_id):
        """
        Create new request.
        
        """
        # here we randonly choose a place for the request
        # origin
        ox,oy = self.city.create_request_coords()
        # destination
        dx,dy = self.city.create_request_coords((ox, oy))
        
        r = Request([ox,oy],[dx,dy],self.latest_request_id,self.time)
        
        # add to request storage
        self.requests[self.latest_request_id]=r 
        # add to free users
        self.requests_pending.append(self.latest_request_id)
        
        self.latest_request_id+=1

        
    def go_to_base(self, taxi_id ,bcoords):
        """
        This function sends the taxi to the base rom wherever it is.
        """
        # actual coordinates
        acoords = [self.taxis[taxi_id].x,self.taxis[taxi_id].y]
        # path between actual coordinates and destination
        path = self.city.create_path(acoords,bcoords)
        # erase path memory
        self.taxis[taxi_id].with_passenger=False
        self.taxis[taxi_id].to_request=False
        self.taxis[taxi_id].available=True
#        print("Erasing path memory, Taxi "+str(taxi_id)+".")
        self.taxis[taxi_id].next_destination = Queue()
        # put path into taxi path queue
#        print("Filling path memory, Taxi "+str(taxi_id)+". Path ",path)
        for p in path:
            self.taxis[taxi_id].next_destination.put(p)
        
    def assign_request(self, request_id):
        """
        This is a sample matching function that assigns the nearest available
        taxi to a user with a random (Gauss) destination.
        """
        # select user
        r = self.requests[request_id]
        
        # search for nearest free taxi
        possible_taxi_ids = self.find_nearest_available_taxis([r.ox,r.oy])
        
        # if there was one
        if len(possible_taxi_ids)>0:
            # select taxi
            taxi_id = choice(possible_taxi_ids)
            t = self.taxis[taxi_id]
            
            # pair the match
            t.actual_request_executing=request_id
            r.taxi_id=taxi_id
            
            # remove taxi from the available ones
            self.city.A[t.x,t.y].remove(taxi_id)
#            print("\tRemoving taxi "+str(taxi_id))
            self.taxis_available.remove(taxi_id)
            t.with_passenger=False
            t.available=False
            t.to_request=True
            
            # mark taxi as moving to request
            self.taxis_to_request.append(taxi_id)

            # forget the path that has been assigned
#            print("Erasing path memory, Taxi "+str(taxi_id)+".")
            t.next_destination = Queue()
            # create new path: to user, then to destination

            path = self.city.create_path([t.x,t.y],[r.ox,r.oy])+\
                self.city.create_path([r.ox,r.oy],[r.dx,r.dy])[1:]
#            print("Filling path memory, Taxi "+str(taxi_id)+". Path",path)
            for p in path:
                t.next_destination.put(p)
                
            # update taxi state in taxi storage
            self.taxis[taxi_id]=t
            
            # remove it from the free users place    
            self.requests_pending.remove(request_id)
            self.requests_in_progress.append(request_id)
            
            # update request state
            self.requests[request_id]=r
            
            if self.log:
                print("\tM request "+str(request_id)+" taxi "+str(taxi_id))
    
        
    def pickup_request(self, request_id):
        """
        Pick up passenger.
        
        Parameters
        ----------
        
        request_id : int
        """
        
        # mark pickup timestamp
        r=self.requests[request_id]
        r.pickup_timestamp=self.time
        t=self.taxis[r.taxi_id]
        
        self.taxis_to_request.remove(r.taxi_id)
        self.taxis_to_destination.append(r.taxi_id)
        
        # change taxi state to with passenger
        t.to_request=False
        t.with_passenger=True
        t.available=False
        
        # set request waiting time
        r.waiting_time = self.time - r.request_timestamp
        
        # update request and taxi instances
        self.requests[request_id]=r
        self.taxis[r.taxi_id]=t
        if self.log:
            print('\tP '+"request "+str(request_id)+' taxi '+str(t.taxi_id))
    
    def dropoff_request(self,request_id):
        """
        Drop off passenger, when taxi reached request destination.
        
        """
        
        # mark dropoff timestamp
        r=self.requests[request_id]
        r.dropoff_timestamp=self.time
        t=self.taxis[r.taxi_id]
        
        # change taxi state to available
        t.with_passenger=False
        t.available=True
        t.actual_request_executing=None
        
        # update taxi lists
        self.city.A[t.x,t.y].append(r.taxi_id)
        self.taxis_to_destination.remove(r.taxi_id)
        self.taxis_available.append(r.taxi_id)
        
        # udate request lists
        self.requests_in_progress.remove(request_id)
        t.requests_completed.append(request_id)
        self.requests_fulfilled.append(request_id)
        
        # update request and taxi instances
        self.requests[request_id]=r
        self.taxis[r.taxi_id]=t
        if self.log:
            print("\tD request "+str(request_id)+' taxi '+str(t.taxi_id))
    
    def find_nearest_available_taxis(
            self,
            source,
            mode = "nearest",
            radius = None):
        """
        This function lists the available taxis according to mode.

        Parameters
        ----------

        source : tuple, no default
            coordinates of the place from which we want to determine the nearest
            possible taxi

        mode : str, default "nearest"
            determines the mode of taxi listing
                * "nearest" lists only the nearest taxis, returns a list where there \
                are all taxis at the nearest possible distance from the source

                * "circle" lists all taxis within a certain distance of the source

        radius : int, optional
            if mode is "circle", gives the circle radius
        """
        frontier = [source]
        visited = []
        possible_plate_numbers = []

        distance = 0
        while (distance<=self.hard_limit):
            # check available taxis in given nodes
            for x,y in list(frontier):
                visited.append((x,y)) # mark the coordinate as visited
                for t in self.city.A[x,y]: # get all available taxis there
                    possible_plate_numbers.append(t)
            # if we visited everybody, break
            if len(visited)==self.city.n*self.city.m:
                if self.log:
                    print("\tNo available taxis at this timepoint!")
                break
            # if we got available taxis in nearest mode, break
            if ((mode=="nearest") and (len(possible_plate_numbers)>0)):
                break
            # if we reached our desired depth, break
            if ((mode=="circle") and (distance>radius)):
                break
            # if not, move on to next depth
            else:
                new_frontier = set()
                for f in frontier:
                    new_frontier = \
                        new_frontier.union(self.city.neighbors(f)).difference(set(visited))
                frontier = list(new_frontier)
                distance+=1

        return possible_plate_numbers

    def plot_simulation(self):
        """
        Draws current state of the simulation on the predefined grid of the class.
        
        Is based on the taxis and requests and their internal states.
        """
        
        self.init_canvas()
        
        for i,taxi_id in enumerate(self.taxis.keys()):
            t = self.taxis[taxi_id]
            
            # plot a circle at the place of the taxi
            self.canvas_ax.plot(t.x,t.y,'o',ms=10,c=self.cmap(self.taxi_colors[i]))
            
            if self.show_map_labels:
                self.canvas_ax.annotate(
                    str(i),
                    xy = (t.x,t.y),
                    xytext = (t.x,t.y),
                    ha='center',
                    va='center',
                    color='white'
                )
            
            # if the taxi has a path ahead of it, plot it
            if (t.next_destination.qsize()!=0):
                path=np.array([[t.x,t.y]]+list(t.next_destination.queue))
                if len(path)>1:
                    xp,yp=path.T
                    # plot path
                    self.canvas_ax.plot(
                        xp,
                        yp,
                        '-',
                        c=self.cmap(self.taxi_colors[i])
                    )
                    # plot a star at taxi destination
                    self.canvas_ax.plot(
                        path[-1][0],
                        path[-1][1],
                        '*',
                        ms=5,
                        c=self.cmap(self.taxi_colors[i])
                    )
                 
            # if a taxi serves a request, put request on the map
            request_id = t.actual_request_executing
            if (request_id!=None) and (not t.with_passenger):
                r = self.requests[request_id]
                self.canvas_ax.plot(
                    r.ox,
                    r.oy,
                    'ro',
                    ms=3        
                )
                if self.show_map_labels:
                    self.canvas_ax.annotate(
                        request_id,
                        xy=(r.ox,r.oy),
                        xytext=(r.ox-0.2,r.oy-0.2),
                        ha='center',
                        va='center'
                    )
                
        #plot taxi base
        self.canvas_ax.plot(
            self.city.base_coords[0],
            self.city.base_coords[1],
            'ks',
            ms=15
        )
        
        # plot pending requests
        if self.show_pending:
            for request_id in self.requests_pending:
                self.canvas_ax.plot(
                    self.requests[request_id].ox,
                    self.requests[request_id].oy,
                    'ro',
                    ms=3,
                    alpha=0.5
                )
        
        self.canvas.show()
                
            
    def move_taxi(self,taxi_id):
        """
        Move a taxi one step forward according to its path queue.
        
        Update taxi position on availablity grid, if necessary.
        
        Parameters
        ----------
        
        taxi_id : int
            unique id of taxi that we want to move
        """
        t=self.taxis[taxi_id]
        try:
            # move taxi one step forward    
            move = t.next_destination.get_nowait()
            
            old_x = t.x
            old_y = t.y
            
            t.x = move[0]
            t.y = move[1]
            
            if t.with_passenger:
                t.useful_travel_time+=1
            else:
                t.empty_travel_time+=1
            
            # move available taxis on availability grid
            if t.available:
                self.city.A[old_x,old_y].remove(taxi_id)
                self.city.A[t.x,t.y].append(taxi_id)
    
            # update taxi instance
            if self.log:
                print("\tF moved taxi "+str(taxi_id)+" remaining path ",list(t.next_destination.queue),"\n",end="")
        except:
            self.taxis[taxi_id].waiting_time+=1
        
        self.taxis[taxi_id]=t

    def evaluate_metrics(self):
        """
        Returns metrics for taxis and requests on its call.
        
        Outputs a dictionary that stores these metrics and the timestamp of the call.
        
        Output
        ------
            
        timestamp: int
            the timestamp of the measurement
            
        avg_req_length: list of floats
            average trip lengths per taxi

        avg_req_price: list of floats
            average trip price per taxi (including the fixed price and fare per distance)
        
        std_req_length: list of floats
            standard deviation of trip lengths per taxi
            
        sum_req: list of ints
            overall trip distaces taken by taxis
            
        online ratio: list of floats
            ratio of useful travel time from overall time for taxis
            online/(online+empty_travel+waiting)
            
        empty_travel_vs_waiting: list of floats
            ratio of empty travelling from overall empty time
            (waiting/(empty_travel+waiting))
            
        completed_request_ratio: float
            percentage of requests completed from all requests
            
        avg_waiting_time: float
            average waiting time of completed requests in the last 100 timesteps
            
        trip_lengths: list of ints
            lengths of all completed requests up to the timestamp
            
        """
        
        # for the taxis
        
        # average trip lengths per taxi
        # standard deviation of trip lengths per taxi
        avg_req_length = []
        std_req_length = []
        sum_req = []
        avg_req_price = []
        online_ratio = []
        empty_travel_vs_waiting = []
        
        
        for taxi_id in self.taxis:
            taxi = self.taxis[taxi_id]
            req_lengths = []
            for request_id in taxi.requests_completed:
                r = self.requests[request_id]
                length = np.abs(r.dy-r.oy)+np.abs(r.dx-r.ox) 
                req_lengths.append(length)
            req_prices = [length * self.price_per_dist + self.price_fixed for length in req_lengths]
            avg_req_price.append(np.mean(req_prices))
            avg_req_length.append(np.mean(req_lengths))
            std_req_length.append(np.std(req_lengths))
            sum_req.append(np.sum(req_lengths))
            
            u = taxi.useful_travel_time
            w = taxi.waiting_time
            e = taxi.empty_travel_time
            
            online_ratio.append(u/(u+w+e))
            empty_travel_vs_waiting.append(w/(w+e))
            
        # for the requests
        
        completed_request_ratio = 0
        total = 0
        waiting_times = []
        lengths = []
        
        for request_id in self.requests:
            r = self.requests[request_id]
            if r.dropoff_timestamp!=None:
                completed_request_ratio+=1
                lengths.append(np.abs(r.dy-r.oy)+np.abs(r.dx-r.ox))
            total+=1
            # to forget hsitory
            # system-level waiting time peak detection
            # it would not be sensible to include all previous waiting times
            if (self.time-r.request_timestamp)<100:
                waiting_times.append(r.waiting_time)
        
        completed_request_ratio = completed_request_ratio/total
        avg_waiting_time = np.mean(waiting_times)
        
        return {
            "timestamp":self.time,
            "avg_req_length":avg_req_length,#p
            "avg_req_price":avg_req_price,
            "std_req_length":std_req_length,#p
            "sum_req":sum_req,#p
            "online_ratio":online_ratio,#p
            "empty_travel_vs_waiting":empty_travel_vs_waiting,#p
            "completed_request_ratio" : completed_request_ratio,#number
            "avg_waiting_time": avg_waiting_time,#number
            "trip_lengths" : lengths #p
            }
        
    def step_batch(self,num_steps,run_id,do_plot=True,fig_path="figs"):
        """
        Forwards time in given batch, and creates figures from the batch run.
        
        Parameters
        ----------
        
        num_steps : int
            number of timesteps to take
            
        run_id : str
            an id of the run with a current config
            it will be used in the figure filenames
            
        fig_path : str, optional, default figs
            in which folder to save the figures
        
        """
        
        # tick the clock
        for i in range(num_steps):
            self.step_time("")
        
        # get metrics
        data = self.evaluate_metrics()
        
        if do_plot:
            # plot metrics
            plt.close('all')
            canvas = plt.figure(figsize=(10,7))
            canvas.suptitle("Simulation (time: "+str(self.time)+", taxis: "+\
                 str(self.num_taxis)+\
                 ", request rate: %.2f)\n completed request ratio %.2f,average waiting time %.5f" \
                % (
                        self.request_rate,data['completed_request_ratio'],
                        data['avg_waiting_time']
                        )
                )
            ax = [canvas.add_subplot(2,3,i) for i in range(1,7)]
            ax[0].hist(data['sum_req'])
            ax[0].set_xlabel("Total trip length per taxi")
            ax[1].hist(list(filter(lambda x: not np.isnan(x),data['avg_req_length'])))
            ax[1].set_xlabel("Average trip length per taxi")
            ax[2].hist(list(filter(lambda x: not np.isnan(x),data['std_req_length'])))
            ax[2].set_xlabel("Std of trip lengths per taxi")
            ax[3].hist(list(filter(lambda x: not np.isnan(x),data['online_ratio'])))
            ax[3].set_xlabel("Online to empty ratio")
            ax[4].hist(list(filter(lambda x: not np.isnan(x),data['empty_travel_vs_waiting'])))
            ax[4].set_xlabel("Waiting to empty ratio")
            ax[5].hist(list(filter(lambda x: not np.isnan(x),data['trip_lengths'])))
            ax[5].set_xlabel("Trips lengths")
            
            # save figure
            canvas.savefig(fig_path+"/run"+run_id+"_time_"+str(self.time)+".pdf")
        return data
    


    def run_batch(self,run_id,num_iter,batch_size,do_plot=True,fig_path="figs"):
        """
        Create a batch run, where at each batch step, a plot is made from the data.
        
        Parameters
        ----------
        
        run_id : str
            id that stands for simulation
            
        num_iter : int
            how many times to run the batch
            
        batch_size : int
            how many timesteps to take in one round
            
        fig_path : str, optional, default figs
            where to save the plots
        """
        t = []
        w = []
        fields = set()
        results = []
        for i in range(num_iter):
            data = self.step_batch(batch_size,run_id,do_plot=do_plot,fig_path=fig_path)
            t.append(data["timestamp"])
            w.append(data["avg_waiting_time"])
            results.append(data)
            fields = fields.union(set(data.keys()))
        data_path = 'results'
        f = open(data_path + '/run' + run_id + 'data.pkl', 'wb')
        pickle.dump(results, f)
        f.close()
        if do_plot:    
            # plot metrics
            canvas = plt.figure(figsize=(10,7))
            canvas.suptitle("Simulation (time: "+str(self.time)+", taxis: "+\
                 str(self.num_taxis))
            ax = canvas.add_subplot(1,1,1)
            ax.plot(t,w,'ro-')
            ax.set_xlabel("Timestamp")
            ax.set_ylabel("Average waiting time")
            # save figure
            canvas.savefig(fig_path+"/run"+run_id+"_waiting_time.pdf")

            for field in fields:
                if field == 'timestamp': continue
                plt.close('all')
                canvas = plt.figure(figsize=(10,7))
                canvas.suptitle("Simulation (time: "+str(self.time)+", taxis: "+\
                     str(self.num_taxis))
                ax = canvas.add_subplot(1,1,1)
                if type(results[0][field]) == list:
                    temp_results = [np.array(res[field]) for res in results]
                    y = [np.mean(res[np.logical_not(np.isnan(res))]) for res in temp_results]
                else:
                    y = [r[field] for r in results]
                ax.plot(t,y,'ro-')
                ax.set_xlabel('Timestamp')
                ax.set_ylabel(field)
                # save figure
                canvas.savefig(fig_path+"/run"+run_id+"_" + field + ".pdf")
        
            
    def step_time(self,handler):
        """
        Ticks simulation time by 1.
        """

        if self.log:
            print("timestamp "+str(self.time))
        
        # move every taxi one step towards its destination
        for i,taxi_id in enumerate(self.taxis.keys()):
            self.move_taxi(taxi_id)
            t = self.taxis[taxi_id]

            # if a taxi can pick up its passenger, do it
            if (taxi_id in self.taxis_to_request):
                r = self.requests[t.actual_request_executing]
                if ((t.x==r.ox) and (t.y==r.oy)):
                    self.pickup_request(t.actual_request_executing)
            # if a taxi can drop of its passenger, do it
            elif (taxi_id in self.taxis_to_destination):
                r = self.requests[t.actual_request_executing]
                if (t.x==r.dx) and (t.y==r.dy):
                    self.dropoff_request(r.request_id)
                    self.go_to_base(taxi_id,self.city.base_coords)
        
        # generate requests
        test = np.random.rand()
        if test<self.request_rate:
            self.add_request(self.latest_request_id)    

        # match requests to available taxis, if possible
        rp_list = self.requests_pending
        for request_id in rp_list:
            self.assign_request(request_id)

        # step time
        if self.show_plot:
            self.plot_simulation()
        self.time+=1