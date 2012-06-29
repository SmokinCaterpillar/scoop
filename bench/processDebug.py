from __future__ import print_function
import sys
from collections import OrderedDict, namedtuple
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import itertools
import os
import argparse

TaskId = namedtuple('TaskId', ['worker', 'rank'])
FutureId = namedtuple('FutureId', ['worker', 'rank'])

parser = argparse.ArgumentParser(description='Analyse the debug info')
parser.add_argument("--inputdir", help='The directory containing the debug info',
        default="debug")

parser.add_argument("--prog", choices=["all", "broker", "density", "queue"],
        default="all", help="The output graph")

parser.add_argument("--output", help="The filename for the output graphs",
        default="debug.png")


args = parser.parse_args()


def getWorkersName(data):
    """Returns the list of the names of the workers sorted alphabetically"""
    names = [fichier for fichier in data.keys()]
    names.sort()
    names.remove("broker")
    return names


def importData(directory):
    """Parse the input files and return two dictionnaries"""
    dataTask = OrderedDict()
    dataQueue = OrderedDict()
    for fichier in os.listdir(directory):
        with open(directory+"/"+fichier, 'r') as f:
            splitFile = fichier.split('-')
            fileType = splitFile[1]
            fileName = splitFile[0]
            if fileType == "QUEUE":
                dataQueue[fileName] = eval(f.read())
            else:
                dataTask[fileName] = eval(f.read())
    return dataTask, dataQueue

def stepSize(startTime, endTime, points):
    step = int((endTime - startTime)/points)
    if step == 0:
        return 1
    else:
        return step

def timeRange(startTime, endTime, points):
    return range(int(startTime), int(endTime), stepSize(startTime, endTime,
        points))

def getTimes(dataTasks):
    """Get the start time and the end time of data in milliseconds"""
    start_time = 9999999999999999999999999; end_time = 0
    for fichier, vals in dataTask.items():
        try:
            if type(vals) == dict:
                tmp_start_time = min([a['start_time'] for a in vals.values()])[0]
                if tmp_start_time < start_time:
                    start_time = tmp_start_time
                tmp_end_time = max([a['end_time'] for a in vals.values()])[0]
                if tmp_end_time > end_time:
                    end_time = tmp_end_time
        except ValueError:
            continue
    return 1000 * start_time, 1000 * end_time



def WorkerDensity(dataTasks):
    """Return the worker density data for the graph."""

    start_time, end_time = getTimes(dataTasks)
    graphdata = []

    for name in getWorkersName(dataTasks):
        vals = dataTasks[name]
        if type(vals) == dict:
            # Data from worker
            workerdata = []
            print("Ploting density map for {}".format(name))
            # We only have 800 pixels
            for graphtime in timeRange(start_time, end_time, 800):
                workerdata.append(sum([a['start_time'][0] <= float(graphtime) /
                    1000. <= a['end_time'][0] for a in vals.values()]))
            graphdata.append(workerdata)
    return graphdata

def plotDensity(dataTask, scale, filename):
    # Worker density graph
    def format_worker(x, pos=None):
        """This function is used as a formater"""
        return dataTask.keys()[x]

    graphdata = WorkerDensity(dataTask)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0 + 0.15 * box.width, box.y0, box.width, box.height])
    cax = ax.imshow(graphdata, interpolation='nearest', aspect='auto')
    plt.xlabel('time ({})'.format(scale)); plt.ylabel('Queue Length'); ax.set_title('Work density')
    ax.yaxis.set_ticks(range(len(graphdata)))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_worker))
    cbar = fig.colorbar(cax)
    fig.savefig(filename)

def plotBrokerQueue(dataTask, filename):
    # Broker queue length graph
    plt.figure()
    plt.subplot(211)
    for fichier, vals in dataTask.items():
        if type(vals) == list:
            # Data is from broker
            plt.plot(zip(*vals)[0], zip(*vals)[2], linewidth=1.0, marker='o', label=fichier)   
    plt.title('Queue length in time')
    plt.ylabel('Tasks')

    plt.subplot(212)
    for fichier, vals in dataTask.items():
        if type(vals) == list:
            # Data is from broker
            plt.plot(zip(*vals)[0], zip(*vals)[3], linewidth=1.0, marker='o', label=fichier)
    plt.xlabel('time (s)')
    plt.ylabel('Requests')
    plt.savefig(filename)

def plotWorkerQueue(dataQueue, filename):
    # workers Queue length Graph
    fig = plt.figure()
    ax = fig.add_subplot(111)

    for fichier, vals in dataQueue.items():
        ax.plot(*zip(*vals), label=fichier)
    plt.xlabel('time(s)'); plt.ylabel('Queue Length')
    plt.title('Queue length throught time')
    fig.savefig(filename)

def getWorkerInfo(dataTask):
    # total work time by worker
    workertime = []
    workertasks = []
    for fichier, vals in dataTask.items():
        if type(vals) == dict:
            #workers_names.append(fichier)
            # Data from worker
            totaltime = sum([a['executionTime'] for a in vals.values()])
            totaltasks = sum([1 for a in vals.values()])
            workertime.append(totaltime)
            workertasks.append(totaltasks)
    return workertime, workertasks

def plotWorkerTime(workertime,worker_names, filename):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ind = range(len(workertime))
    width = 0.35

    print(ind, workertime, width)

    rects = ax.bar(ind, workertime, width)
    ax.set_ylabel('WorkedTime')
    ax.set_title('Worked time for each worker')
    ax.set_xticks(ind)
    ax.set_xticklabels(worker_names)

    fig.savefig(filename)


def plotWorkerTask(workertask,worker_names, filename):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ind = range(len(workertask))
    width = 0.35

    rects = ax.bar(ind, workertask, width)
    ax.set_ylabel('Tasks')
    ax.set_title('Number of tasks executed by each worker')
    #ax.set_xticks([x+width for x in ind])
    ax.set_xticklabels(worker_names)

    fig.savefig(filename)

if __name__ == "__main__":
    dataTask, dataQueue = importData(args.inputdir)

    if args.prog == "density" or args.prog == "all":
        plotDensity(dataTask, "s", "density_" + args.output)

    if args.prog == "broker" or args.prog == "all":
        plotBrokerQueue(dataTask, "broker_" + args.output)

    if args.prog == "queue" or args.prog == "all":
        plotWorkerQueue(dataQueue, "queue_" + args.output)

    if args.prog == "time" or args.prog == "all":
        workerTime, workerTasks = getWorkerInfo(dataTask)
        plotWorkerTime(workerTime, getWorkersName(dataTask), "time_" + args.output)

    if args.prog == "task" or args.prog == "all":
        workerTime, workerTasks = getWorkerInfo(dataTask)
        plotWorkerTask(workerTasks, getWorkersName(dataTask), "task_" + args.output)