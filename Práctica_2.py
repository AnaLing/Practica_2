
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1  #tenemos coches que van en dirección sur y otros en dirección norte
NORTH = 0

NCARS = 15
NPED = 10
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 3 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRGIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        self.ncarsnorth = Value('i', 0)
        self.ncarssouth = Value('i', 0)
        self.npeds = Value('i', 0)
        
        self.ncarsnorth_waiting = Value('i', 0) #variable condición para la cantidad de coches en dirección norte esperando
        self.ncarssouth_waiting = Value('i', 0)
        self.npeds_waiting = Value('i', 0)

        self.no_carsnorth = Condition(self.mutex)
        self.no_carssouth = Condition(self.mutex) 
        self.no_peds = Condition(self.mutex) 


    def are_no_carsnorth(self):  #nos dice si hay coches en dirección norte 
        return self.ncarsnorth.value == 0 and self.ncarsnorth_waiting.value == 0
    
    
    def are_no_carssouth(self):  #nos dice si hay coches en dirección sur 
        return self.ncarssouth.value == 0 and self.ncarssouth_waiting.value == 0


    def are_no_peds(self): #nos dice si hay caminantes 
        return self.npeds.value == 0 and self.npeds_waiting.value == 0
            
            
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        if direction == 0: 
          self.ncarsnorth_waiting.value += 1
          self.no_carssouth.wait_for(self.are_no_carssouth) #si la dirección es norte, debe esperar a que no haya coches en dirección sur ni caminantes 
          self.no_peds.wait_for(self.are_no_peds)
          self.ncarsnorth_waiting.value -= 1
          self.ncarsnorth.value += 1
        
        else: 
          self.ncarssouth_waiting.value += 1
          self.no_carsnorth.wait_for(self.are_no_carsnorth) #si la dirección es sur, no puede haber coches en dirección norte ni caminantes 
          self.no_peds.wait_for(self.are_no_peds)
          self.ncarssouth_waiting.value -= 1
          self.ncarssouth.value += 1
        
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        
        if direction == 0:
          self.ncarsnorth.value -= 1
          if self.ncarsnorth.value == 0:
            self.no_carsnorth.notify_all() #notifica que ya no hay coches en dirección norte
        else:
          self.ncarssouth.value -= 1
          if self.ncarssouth.value == 0:
            self.no_carssouth.notify_all() #notifica que los coches en dirección sur han dejado el puente
          
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        self.npeds_waiting.value += 1
        self.no_carsnorth.wait_for(self.are_no_carsnorth) #los caminantes deben esperar a que no haya coches 
        self.no_carssouth.wait_for(self.are_no_carssouth)
        self.npeds_waiting.value -= 1
        self.npeds.value += 1 
        
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        self.npeds.value -= 1
        if self.npeds.value == 0:
          self.no_peds.notify_all() #notifica que no hay caminantes en el puente
          
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    pass

def delay_car_south() -> None:
    pass

def delay_pedestrian() -> None:
    pass

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()
