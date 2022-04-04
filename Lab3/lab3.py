# PythonSim imports
import SimClasses as sc
import SimFunctions as sf
import SimRNG as rng

# Python package imports
import math
import pandas
import numpy as np
import csv

f = open('TISdata.csv','w', newline= '') 
fwriter = csv.writer(f) 

TheQueues = []
TheResources = []


#initialize
sc.Clock = 0
ZSimRNG = rng.InitializeRNSeed()
Calendar = sc.EventCalendar()
RunLength = 500.0 # change from 2000 to 500

TISRecords = [] 

NumAgents = [4,3]
FAgents = sc.Resource()
FAgents.SetUnits(NumAgents[0])
TheResources.append(FAgents)
CAgents = sc.Resource()
CAgents.SetUnits(NumAgents[1])
TheResources.append(CAgents)

WaitTime = sc.DTStat()
WaitTimeAvg = []

FQueue = sc.FIFOQueue()
TheQueues.append(FQueue)
CQueue = sc.FIFOQueue()
TheQueues.append(CQueue)

# Parameters
STPhases = [2,3]
STMean = 5.0
STStreams = [3,4]
ATMean = 1.0
ProbType = [0.59, 0.41]


def Arrival():
    # Schedule the next arrival
    sf.Schedule(Calendar,"Arrival",rng.Expon(ATMean,1))
    
    sf.Schedule(Calendar,"SelectType",rng.Uniform(0.1,0.2,2))
    
def SelectType():
    # Customers reveal their types
    U = rng.Uniform(0,1,2) 
    
    if U<ProbType[0]: #This is the case when the customer is finance type
        Customer = sc.Entity2(0)
        if(TheResources[0].CurrentNumBusy < NumAgents[0]): 
            TheResources[0].Seize(1)
            sf.SchedulePlus(Calendar,"EndOfService",rng.Erlang(STPhases[0],STMean,STStreams[0]),Customer)
        else:
            TheQueues[0].Add(Customer)
    else:
        Customer = sc.Entity2(1)
        if(TheResources[1].CurrentNumBusy < NumAgents[1]): 
            TheResources[1].Seize(1)
            sf.SchedulePlus(Calendar,"EndOfService",rng.Erlang(STPhases[1],STMean,STStreams[1]),Customer)
        else:
            TheQueues[1].Add(Customer)
        
        
def EndOfService(OldCustomer):  
    WaitTime.Record(sc.Clock-OldCustomer.CreateTime)
    TISRecords.append(sc.Clock - OldCustomer.CreateTime)
    if TheQueues[OldCustomer.Type].NumQueue() > 0:
        Customer = TheQueues[OldCustomer.Type].Remove()
        sf.SchedulePlus(Calendar,"EndOfService",rng.Erlang(STPhases[OldCustomer.Type],STMean,STStreams[OldCustomer.Type]),Customer)
    else:
        TheResources[OldCustomer.Type].Free(1)


for reps in range(0,200,1):
    TISRecords = [] 
    sf.SimFunctionsInit(Calendar)
    sf.Schedule(Calendar,"Arrival",rng.Expon(ATMean, 1))
    sf.Schedule(Calendar,"EndSimulation",RunLength)
    
    while Calendar.N() > 0:
        NextEvent = Calendar.Remove()
        sc.Clock = NextEvent.EventTime
        if NextEvent.EventType == "Arrival":
            Arrival()
        elif NextEvent.EventType == "SelectType":
            SelectType()
        elif NextEvent.EventType == "EndOfService":
            EndOfService(NextEvent.WhichObject)
        elif NextEvent.EventType == "EndSimulation":
            break
    fwriter.writerow(TISRecords)        
    WaitTimeAvg.append(WaitTime.Mean())

f.close() 
print("Mean time spent is", np.mean(WaitTimeAvg), "minutes.")
print("Its standard error is", np.std(WaitTimeAvg)/np.sqrt(10), "minutes.")


