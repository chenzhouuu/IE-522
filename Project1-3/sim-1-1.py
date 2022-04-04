import SimClasses as sc
import SimFunctions as sf
import SimRNG as rng
import math
import pandas as pd
import numpy as np
np.random.seed(123)

# parameters

RunLength = 330.0
WarmUp = 30.0
NumReps = 10

MeanTOT = 1.41
MeanTCM = 0.09
MeanTBA = [5.12, 11.68, 4.27, 6.88, 5.15, 5.07, 3.81]
number_server = 2

class Simulation:
    def __init__(self) -> None:

        sc.Clock = 0.0
        self.ZSimRNG = rng.InitializeRNSeed()
        self.BranchQueues = [sc.FIFOQueue() for _ in range(7)]
        self.RotQueues = sc.FIFOQueue()

        self.WaitTime = sc.DTStat()
        self.Prob7 = sc.DTStat()   # probability of waiting longer than 7 seconds
        self.Server = sc.Resource()
        self.Calendar = sc.EventCalendar()
        self.Occupation = [sc.Resource() for _ in range(7)]
        for i in range(7):
            self.Occupation[i].SetUnits(1) 
        self.Server.SetUnits(number_server)

        self.WaitTimeAvg = []
        self.Prob7Avg = [] 

    def Arrival(self):
        
        # choose branch
        p = 1 / np.array(MeanTBA) / np.sum(1 / np.array(MeanTBA))
        index = np.random.choice([0,1,2,3,4,5,6], 1, p=p)[0]
        
        Customer = sc.Entity2(index)
        if self.Occupation[index].CurrentNumBusy == 0:
            self.Occupation[index].Seize(1)
            sf.SchedulePlus(self.Calendar, "MoveToOrder", 0, Customer)     
        else:
            self.BranchQueues[index].Add(Customer)
        
        sf.Schedule(self.Calendar, "Arrival", rng.Expon(1 / np.sum(1 / np.array(MeanTBA)), 1))


    def MoveToOrder(self, Customer):
        if self.Server.CurrentNumBusy < self.Server.NumberOfUnits:
            self.WaitTime.Record(sc.Clock - Customer.CreateTime)
            self.Prob7.Record((sc.Clock - Customer.CreateTime) > 7/60)
            self.Server.Seize(1)
            sf.SchedulePlus(self.Calendar, "Departure", rng.Expon(MeanTOT, 1), Customer)
            
        else:
            self.RotQueues.Add(Customer)
    
    def Departure(self, OldCustomer):
        self.Server.Free(1)
        if self.RotQueues.NumQueue() > 0:
            self.Server.Seize(1)
            Customer = self.RotQueues.Remove()
            self.WaitTime.Record(sc.Clock - Customer.CreateTime)
            self.Prob7.Record((sc.Clock - Customer.CreateTime) > 7/60)
            sf.SchedulePlus(self.Calendar, "Departure", rng.Expon(MeanTOT, 1), Customer)

        if self.BranchQueues[OldCustomer.Type].NumQueue() > 0:
            BranchCustomer = self.BranchQueues[OldCustomer.Type].Remove()
            sf.SchedulePlus(self.Calendar, "MoveToOrder", rng.Expon(MeanTCM, 1), BranchCustomer)
        else:
            self.Occupation[OldCustomer.Type].Free(1)


    def run(self):
        for reps in range(0,NumReps,1):
            sf.SimFunctionsInit(self.Calendar)
            p = 1 / np.array(MeanTBA) / np.sum(1 / np.array(MeanTBA))
            index = np.random.choice([0,1,2,3,4,5,6], 1, p=p)[0]
            sf.Schedule(self.Calendar, "Arrival", rng.Expon(MeanTBA[index], 1))
            sf.Schedule(self.Calendar, "EndSimulation", RunLength)
            sf.Schedule(self.Calendar, "ClearIt", WarmUp)

            while self.Calendar.N() > 0:
                NextEvent = self.Calendar.Remove()
                sc.Clock = NextEvent.EventTime
                if NextEvent.EventType == "Arrival":
                    self.Arrival()                       
                elif NextEvent.EventType == "MoveToOrder":
                    self.MoveToOrder(NextEvent.WhichObject)
                elif NextEvent.EventType == "Departure":
                    self.Departure(NextEvent.WhichObject)
                elif NextEvent.EventType == "ClearIt":
                    sf.ClearStats() 
                elif NextEvent.EventType == "EndSimulation":
                    break
            
            
            
            self.WaitTimeAvg.append(self.WaitTime.Mean())
            self.Prob7Avg.append(self.Prob7.Mean())
        output = pd.DataFrame(
            {
                "WaitTimeAvg": self.WaitTimeAvg,
                "SpendTimeMoreThanSeven": self.Prob7Avg
            }
        )
        print("Means")
        print(output.mean())
        
        print("Standard Deviation")
        print(np.sqrt(output.var()))

        print("95% CI Half-Width")
        print(1.96*np.sqrt(output.var()/len(output)))
        output.to_csv('results.csv')

def main():
    sim = Simulation()
    sim.run()

if __name__ == "__main__":
    main()