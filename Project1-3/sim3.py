# -*- coding: utf-8 -*-
import SimFunctions
import SimClasses
import SimRNG
import numpy as np
import csv
import pandas as pd

np.random.seed(123)
f = open('TISdata.csv','w', newline= '') 
fwriter = csv.writer(f) 
# Initialization
SimClasses.Clock = 0
ZSimRNG = SimRNG.InitializeRNSeed()
Calendar = SimClasses.EventCalendar()

# statistics
Wait = SimClasses.DTStat()
ExcessProb = SimClasses.DTStat()   # probability of waiting longer than 5 minutes

# across-replication statistics
TotalWait = []
TotalExcessProb = []
TISRecords = []

# parameters
CallCenterUnits = 7
MeanTBA = [5.12, 11.68, 4.27, 6.88, 5.15, 5.07, 3.81] #mins
MeanNew = np.mean(MeanTBA)
NumBranch = 13
for _ in range(NumBranch - 7):
    MeanTBA.append(MeanNew)

MeanOT = 1.41
MeanMT = 0.09
RunLength = 90 + 600
WarmUp = 90
NumReps = 10000
print(NumReps)

# lists of queues and resources for all seven branches
BranchQs = []
BranchWindows = [] 

# Create all Queues & Resources
for i in range(0,NumBranch,1):
    Queue = SimClasses.FIFOQueue()
    BranchQs.append(Queue)
    OrderWindow = SimClasses.Resource()
    OrderWindow.SetUnits(1)
    BranchWindows.append(OrderWindow)
    
# ROT resources
VQ = SimClasses.FIFOQueue()
CallCenter = SimClasses.Resource()
CallCenter.SetUnits(CallCenterUnits)

def Arrival(Branch_index): 
    SimFunctions.SchedulePlus(Calendar,"Arrival",SimRNG.Expon(MeanTBA[Branch_index],1),Branch_index)
    
    Customer = SimClasses.Entity2(Branch_index)
    
    if BranchWindows[Branch_index].CurrentNumBusy == 0:
        BranchWindows[Branch_index].Seize(1)
        SimFunctions.SchedulePlus(Calendar,"MoveToOrder",0,Customer)
    else:
        BranchQs[Branch_index].Add(Customer)

def MoveToOrder(Customer):
    # This is the event where the customer arrives to the order board.
    # start recording the wait time here
    Customer.CreateTime = SimClasses.Clock
    
    if CallCenter.CurrentNumBusy < CallCenterUnits:
        CallCenter.Seize(1)
        Wait.Record(0.0)
        ExcessProb.Record(0.0)
        SimFunctions.SchedulePlus(Calendar,"Departure",SimRNG.Expon(MeanOT,1),Customer)
    else:
        VQ.Add(Customer)
   
def Departure(Customer):
    # This event happens when an ROT agent finishes serving a customer
    if VQ.NumQueue()>0:
        NewCustomer = VQ.Remove()
        # collect the wait time
        Wait.Record(SimClasses.Clock - NewCustomer.CreateTime)
        ExcessProb.Record((SimClasses.Clock - NewCustomer.CreateTime > 7 / 60))
        TISRecords.append(SimClasses.Clock - NewCustomer.CreateTime) 
        SimFunctions.SchedulePlus(Calendar,"Departure",SimRNG.Expon(MeanOT,1),NewCustomer)
    else:
        CallCenter.Free(1)
    
    # Check the branch queue of the leaving customer
    if BranchQs[Customer.Type].NumQueue()>0:
        BranchCustomer = BranchQs[Customer.Type].Remove()
        SimFunctions.SchedulePlus(Calendar,"MoveToOrder",SimRNG.Expon(MeanMT,1),BranchCustomer)
    else:
        BranchWindows[Customer.Type].Free(1)

warmup_list = []  
for reps in range(0,NumReps,1):
    
    TISRecords = [] 
    SimFunctions.SimFunctionsInit(Calendar)
    
    # generate the first arrival for each branch
    for ID in range(0,NumBranch,1):
        SimFunctions.SchedulePlus(Calendar,"Arrival",SimRNG.Expon(MeanTBA[ID], 1),ID)
    
    SimFunctions.Schedule(Calendar,"EndSimulation",RunLength)
    SimFunctions.Schedule(Calendar,"ClearIt",WarmUp)
    arrival_count = 0
    while Calendar.N() > 0:
        NextEvent = Calendar.Remove()
        SimClasses.Clock = NextEvent.EventTime
        if NextEvent.EventType == "Arrival":
            Arrival(NextEvent.WhichObject)
            arrival_count += 1
            if arrival_count == 100:
                warmup_list.append(SimClasses.Clock)  
        elif NextEvent.EventType == "MoveToOrder":
            MoveToOrder(NextEvent.WhichObject)
        elif NextEvent.EventType == "Departure":
            Departure(NextEvent.WhichObject) 
        elif NextEvent.EventType == "ClearIt":
            SimFunctions.ClearStats()
        elif NextEvent.EventType == "EndSimulation":
            break
    
    TotalWait.append(Wait.Mean())
    TotalExcessProb.append(ExcessProb.Mean())
    fwriter.writerow(TISRecords)

f.close()

# print('Warmup time: {}'.format(np.mean(warmup_list)))
output = pd.DataFrame(
            {
                "WaitTimeAvg": TotalWait,
                "SpendTimeMoreThanSeven": TotalExcessProb
            }
        )
mean_wt = output['WaitTimeAvg'].mean()
mean_p = output['SpendTimeMoreThanSeven'].mean()

s2_wt = 1 / (NumReps-1) * ((output['WaitTimeAvg'] - mean_wt) ** 2).sum()
s2_p = NumReps / (NumReps -1) * mean_p * (1 - mean_p)
# s2_p = output['SpendTimeMoreThanSeven'].var()
# s_wt = np.sqrt(s2_wt)
# s_p = np.sqrt(s2_p)
s_wt = output['WaitTimeAvg'].std()
s_p = output['SpendTimeMoreThanSeven'].std()
ci_wt = s_wt * 1.96 / np.sqrt(NumReps)
ci_p = s_p * 1.96 / np.sqrt(NumReps)

print("The CI for average waiting time at numberserver = {} is {} pm {}".format(CallCenterUnits, mean_wt, ci_wt))
print("The CI for probability at numberserver = {} is {} pm {}".format(CallCenterUnits, mean_p, ci_p))

print("The relative error for average waiting time at numberserver = {} is {}".format(CallCenterUnits, s_wt / np.sqrt(NumReps) / mean_wt))
print("The relative error for probability at numberserver = {} is {}".format(CallCenterUnits,  s_p / np.sqrt(NumReps) / mean_p))
print('----------------------------')
print(output.mean())
output.to_csv('results_{}.csv'.format(CallCenterUnits))