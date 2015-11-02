import sys
import os.path
sys.path.append(os.path.join('..', 'util'))

import set_compiler
set_compiler.install()

import pyximport
pyximport.install()

import numpy as np
import pylab

import filtering
from timer import Timer
import threading

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

def py_median_3x3(image, iterations=10, num_threads=1):
    ''' repeatedly filter with a 3x3 median '''
    tmpA = image.copy() 
    tmpB = np.empty_like(tmpA)

    for i in range(iterations):
        filtering.median_3x3(tmpA, tmpB, 0, 1)
        # swap direction of filtering
        tmpA, tmpB = tmpB, tmpA

    return tmpA

def py_median_3x3_threads(image, iterations=10, num_threads=1):
    ''' repeatedly filter with a 3x3 median '''
    tmpA = image.copy() 
    tmpB = np.empty_like(tmpA)


    #Initialize the events one event per (threadid, iteration step) tuple
    e = [threading.Event() for _ in range(num_threads*iterations)]
    e = np.reshape(e,(num_threads,iterations))


    # Create the treads, append them into a list
    # this way, it will be easier to join them at the end
    threads = []
    for thread_id in range(num_threads):
    	# create the threads, pass the function and the inputs
        t = threading.Thread(target=filter_image, 
            args=(tmpA, tmpB, iterations, thread_id, num_threads, e))
        threads.append(t)
        # threads start working now
        t.start()
    # kill all the threads because the work is done
    print 'now joining all the threads'
    if e
    map(lambda t: t.join(),threads)

    return tmpA
    
def filter_image(tmpA, tmpB, iterations, thread_id,num_threads, e ):

    
    for i in range(iterations):
        # no wait at 1st iteration
        if i > 0 :
            # if first line just wait for the next one
            if thread_id == 0:
                e[thread_id+1,i-1].wait()
            # if last line just wait for the one before
            elif thread_id == num_threads-1:
                e[thread_id-1,i-1].wait()
            # else wait for line before and after
            else :
                e[thread_id+1,i-1].wait()
                e[thread_id-1,i-1].wait()

        # do the job        
        logging.debug('starting iteration %s with thread_id %s', i, thread_id)
        filtering.median_3x3(tmpA, tmpB, thread_id, num_threads)
        logging.debug('ending iteration %s with thread_id %s',  i, thread_id)


        # swap direction of filtering
        tmpA, tmpB = tmpB, tmpA


        #awakes all the thread waiting for it
        if num_threads>1:
            e[thread_id,i].set()


    return tmpA

def numpy_median(image, iterations=10):
    ''' filter using numpy '''
    for i in range(iterations):
        padded = np.pad(image, 1, mode='edge')
        stacked = np.dstack((padded[:-2,  :-2], padded[:-2,  1:-1], padded[:-2,  2:],
                             padded[1:-1, :-2], padded[1:-1, 1:-1], padded[1:-1, 2:],
                             padded[2:,   :-2], padded[2:,   1:-1], padded[2:,   2:]))
        image = np.median(stacked, axis=2)

    return image


if __name__ == '__main__':
    input_image = np.load('image.npz')['image'].astype(np.float32)

    pylab.gray()

    pylab.imshow(input_image)
    pylab.title('original image')

    pylab.figure()
    pylab.imshow(input_image[1200:1800, 3000:3500])
    pylab.title('before - zoom')

    # verify correctness
    from_cython = py_median_3x3_threads(input_image, iterations=2, num_threads=2)
    from_numpy = numpy_median(input_image, 2)
    assert np.all(from_cython == from_numpy)
    print 'FIRST TEST IS PASSED'
    print 'NOW DOING THE REAL IMAGE PROCESSING'

    with Timer() as t:
        new_image = py_median_3x3_threads(input_image, 10, 8)

    pylab.figure()
    pylab.imshow(new_image[1200:1800, 3000:3500])
    pylab.title('after - zoom')

    print("{} seconds for 10 filter passes.".format(t.interval))
    pylab.show()
