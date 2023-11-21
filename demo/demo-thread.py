import threading  
import queue
import time


worker = 10
workQ=queue.Queue(worker)
def Process(name):
    while True:
        try:  
            task=workQ.get(block=True, timeout=10)
        except queue.Empty:
            break
        print("task: {}".format(task))
        time.sleep(1)
    print("process {} exist".format(name))

threads = []
for i in range(worker):
    t = threading.Thread(target=Process, args=["thread-{}".format(i)])
    t.start()
    threads.append(t)

total = 0
sTime = time.time()
for i in range(100):
    if total % 10 == 0:
        print("{} current {} cost {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), total, time.time()-sTime))
    total = total + 1
    workQ.put(i, block=True, timeout=None)
    
while not workQ.empty():
    pass

for t in threads:
    t.join()
print("{} current {} cost {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), total, time.time()-sTime))
