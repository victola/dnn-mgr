import sys
import numpy as np
import theano
from pylearn2.utils import serial
from pylearn2.datasets.transformer_dataset import TransformerDataset
import cPickle
import GTZAN_dataset

import pdb
def frame_misclass_error(model, dataset):
    """
    Function to compute the frame-level classification error by classifying
    individual frames and then voting for the class with highest cumulative probability
    """

    X = model.get_input_space().make_theano_batch()
    Y = model.fprop( X )
    fprop = theano.function([X],Y)

    n_classes  = dataset.raw.y.shape[1]
    confusion  = np.zeros((n_classes, n_classes))
    n_examples = len(dataset.raw.support)
    n_frames_per_file = dataset.raw.n_frames_per_file

    batch_size = n_frames_per_file
    data_specs = dataset.raw.get_data_specs()
    iterator = dataset.iterator(mode='sequential', 
        batch_size=batch_size, 
        data_specs=data_specs
        )

    i=0
    for el in iterator:

        # display progress indicator
        sys.stdout.write('Classify progress: %2.0f%%\r' % (100*i/float(n_examples)))
        sys.stdout.flush()
    
        fft_data    = np.array(el[0], dtype=np.float32)
        vote_labels = np.argmax(fprop(fft_data), axis=1)
        true_labels = np.argmax(el[1], axis=1)

        for l,v in zip(true_labels, vote_labels):
            confusion[l, v] += 1

        i += batch_size

    total_error = 100*(1 - np.sum(np.diag(confusion)) / np.sum(confusion))
    print ''
    return total_error, confusion

def file_misclass_error(model, dataset):
    """
    Function to compute the file-level classification error by classifying
    individual frames and then voting for the class with highest cumulative probability
    """
    X = model.get_input_space().make_theano_batch()
    Y = model.fprop( X )
    fprop = theano.function([X],Y)

    n_classes  = dataset.raw.y.shape[1]
    confusion  = np.zeros((n_classes, n_classes))
    n_examples = len(dataset.raw.support)
    n_frames_per_file = dataset.raw.n_frames_per_file

    batch_size = n_frames_per_file
    data_specs = dataset.raw.get_data_specs()
    iterator = dataset.iterator(mode='sequential', 
        batch_size=batch_size, 
        data_specs=data_specs
        )

    i=0
    for el in iterator:

        # display progress indicator
        sys.stdout.write('Classify progress: %2.0f%%\r' % (100*i/float(n_examples)))
        sys.stdout.flush()
    
        fft_data     = np.array(el[0], dtype=np.float32)
        frame_labels = np.argmax(fprop(fft_data), axis=1)
        hist         = np.bincount(frame_labels, minlength=n_classes)
        vote_label   = np.argmax(hist) # most used label

        labels = np.argmax(el[1], axis=1)
        true_label = labels[0]
        for entry in labels:
             assert entry == true_label # check for indexing prob

        confusion[true_label, vote_label] += 1

        i+=batch_size

    total_error = 100*(1 - np.sum(np.diag(confusion)) / np.sum(confusion))
    print ''
    return total_error, confusion

def file_misclass_error_topx(model, dataset, topx=3):
    """
    Function to compute the file-level classification error by classifying
    individual frames and then voting for the class with highest cumulative probability

    Check topx most probable results
    """
    X = model.get_input_space().make_theano_batch()
    Y = model.fprop( X )
    fprop = theano.function([X],Y)

    n_classes  = dataset.raw.y.shape[1]
    confusion  = np.zeros((n_classes, n_classes))
    n_examples = len(dataset.raw.support)
    n_frames_per_file = dataset.raw.n_frames_per_file

    batch_size = n_frames_per_file
    data_specs = dataset.raw.get_data_specs()
    iterator = dataset.iterator(mode='sequential', 
        batch_size=batch_size, 
        data_specs=data_specs
        )

    hits = 0
    n = 0
    i=0
    for el in iterator:

        # display progress indicator
        sys.stdout.write('Classify progress: %2.0f%%\r' % (100*i/float(n_examples)))
        sys.stdout.flush()
    
        fft_data     = np.array(el[0], dtype=np.float32)
        frame_labels = np.argmax(fprop(fft_data), axis=1)
        hist         = np.bincount(frame_labels, minlength=n_classes)
        vote_label   = np.argsort(hist)[-1:-1-topx:-1] # most used label

        labels = np.argmax(el[1], axis=1)
        true_label = labels[0]
        for entry in labels:
             assert entry == true_label # check for indexing prob

        if true_label in vote_label:
            hits+=1

        n+=1
        i+=batch_size

    print ''
    return hits/float(n)*100


if __name__ == '__main__':
    
    _, fold_file, model_file = sys.argv
    #fold_file = 'GTZAN_1024-fold-4_of_4.pkl'
    #model_file = './saved-rlu-505050/mlp_rlu-fold-4_of_4.pkl'

    # get model
    model = serial.load(model_file)  

    # get stanardized dictionary  
    which_set = 'test'
    with open(fold_file) as f:
        config = cPickle.load(f)
    
    dataset = TransformerDataset(
        raw = GTZAN_dataset.GTZAN_dataset(config, which_set),
        transformer = GTZAN_dataset.GTZAN_standardizer(config)
        )

    # test error
    #err, conf = frame_misclass_error(model, dataset)
    
    err, conf = file_misclass_error(model, dataset)
    
    print 'test accuracy: %2.2f' % (100-err)
    print 'confusion matrix:'
    print conf/np.sum(conf, axis=1)

    # acc = file_misclass_error_topx(model, dataset, 2)
    # print 'test accuracy: %2.2f' % acc





