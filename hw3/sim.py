from ast import arg
from cv2 import mean
import SimClasses as sc
import SimFunctions as sf
import SimRNG
import numpy as np
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description='Simulation for M/G/c and M/G/c/k')
parser.add_argument('--stationary', default = False, type=bool, help='determine if the arrival is stationary')
parser.add_argument('--runlength', default = 24, type=int, help='running length of the simulation')
parser.add_argument('--numreps', default = 2000, type=int, help='replication of the simulation')
# MeanTBA = 0.1
MeanPT = 1.0 


class Simulation:
    def __init__(self, args) -> None:
        self.ParkingLot = sc.FIFOQueue()
        self.Calendar = sc.EventCalendar()
        self.TimeSpent = sc.DTStat()
        self.MaxCars = 0 # maximum number of cars in the garage
        self.MaxCarsAvg =[]
        self.TimeSpentAvg = [] 
        self.NumCarsAvg = []
        self.NUmCarsT = []
        self.args = args
        self.car_counts_df = pd.read_excel('CarCounts.xls')
        if self.args.stationary: 
            self.MeanTBA = 1 / self.car_counts_df.mean().mean()
        else:
            self.MeanTBA = 1 / self.car_counts_df.mean().values
        
        
    def Arrival(self):
        newCar = sc.Entity()
        self.ParkingLot.Add(newCar)
        if self.MaxCars < self.ParkingLot.NumQueue():
            self.MaxCars = self.ParkingLot.NumQueue()
        if self.args.stationary:
            sf.Schedule(self.Calendar, "Arrival", SimRNG.Expon(self.MeanTBA,1))
        else:
            i = int(sc.Clock % 8)
            sf.Schedule(self.Calendar, "Arrival", SimRNG.Expon(self.MeanTBA[i],1))
        sf.Schedule(self.Calendar, "Departure", SimRNG.Expon(MeanPT,2)) 

    def Departure(self): 
        DepartingCar = self.ParkingLot.Remove() 
        self.TimeSpent.Record(sc.Clock - DepartingCar.CreateTime) 

    def run(self):
        for reps in range(self.args.numreps):
            sf.SimFunctionsInit(self.Calendar)
            self.MaxCars = 0
            
            if self.args.stationary:
                sf.Schedule(self.Calendar, "Arrival", SimRNG.Expon(self.MeanTBA,1))
            else:
                i = int(sc.Clock % 8)
                sf.Schedule(self.Calendar, "Arrival", SimRNG.Expon(self.MeanTBA[i],1))
            sf.Schedule(self.Calendar,"EndSimulation", self.args.runlength) 

            while (self.Calendar.N() > 0):
                NextEvent = self.Calendar.Remove() 
                sc.Clock = NextEvent.EventTime 
                if NextEvent.EventType =="Arrival": 
                    self.Arrival() 
                elif NextEvent.EventType =="Departure": 
                    self.Departure()
                else: # NextEvent.EventType =="EndSimulation" 
                    break    
            
            self.MaxCarsAvg.append(self.MaxCars)
            self.TimeSpentAvg.append(self.TimeSpent.Mean())
            self.NumCarsAvg.append(self.ParkingLot.Mean())
            if sc.Clock // 8 == 0:
                self.NUmCarsT.append(self.ParkingLot)
    
        print(np.mean(self.MaxCarsAvg)) 
        print(np.std(self.MaxCarsAvg)) 
        print(np.mean(self.TimeSpentAvg)) 
        print(np.std(self.TimeSpentAvg)) 
        print(np.mean(self.NumCarsAvg)) 
        print(np.std(self.NumCarsAvg))

        # output = pd.DataFrame( 
        #     {"MaxCarAvg": self.MaxCarsAvg, 
        #     "TimeSpentAvg": self.TimeSpentAvg,  
        #     "NumCarsAvg" : self.NumCarsAvg}) 
        # output.to_csv("MMInf_output.csv", sep=",")  

        print('The estimate of 0.9-quantile of the maximum number of cars is {}'.format(np.quantile(self.MaxCarsAvg, 0.9)))
            
                

def main():
    args = parser.parse_args()  
    
    sc.Clock = 0.0 # initialize the simulation Clock to be 0 
    RunLength = 8.0 # determine the end of the simulation
    sim = Simulation(args)
    sim.run()

if __name__ == "__main__":
    main()