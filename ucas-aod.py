# --------------------------------------------------------
# Fast/er R-CNN
# Licensed under The MIT License [see LICENSE for details]
# Written by Bharath Hariharan
# --------------------------------------------------------

import xml.etree.ElementTree as ET
import os
#import cPickle
import numpy as np
import matplotlib.pyplot as plt

def parse_rec(filename):
    """ Parse a PASCAL VOC xml file """
    tree = ET.parse(filename)
    objects = []
    for obj in tree.findall('object'):
        obj_struct = {}
        obj_struct['name'] = obj.find('name').text
        obj_struct['pose'] = obj.find('pose').text
        obj_struct['truncated'] = int(obj.find('truncated').text)
        obj_struct['difficult'] = int(obj.find('difficult').text)
        bbox = obj.find('bndbox')
        obj_struct['bbox'] = [int(bbox.find('xmin').text),
                              int(bbox.find('ymin').text),
                              int(bbox.find('xmax').text),
                              int(bbox.find('ymax').text)]
        objects.append(obj_struct)

    return objects
def parse_gt(filename):
    objects = []
    with  open(filename, 'r', encoding='utf_16') as f:
        while True:
            line = f.readline()
            if line:
                splitlines = line.strip().split(' ')
                object_struct = {}
                object_struct['name'] = splitlines[8]
                if (len(splitlines) == 9):
                    object_struct['difficult'] = 0
                elif (len(splitlines) == 10):
                    object_struct['difficult'] = 1
                object_struct['bbox'] = [int(float(splitlines[0])),
                                         int(float(splitlines[1])),
                                         int(float(splitlines[4])),
                                         int(float(splitlines[5]))]
                w = int(float(splitlines[4])) - int(float(splitlines[0]))
                h = int(float(splitlines[5])) - int(float(splitlines[1]))
                object_struct['area'] = w * h
                #print('area:', object_struct['area'])
                if object_struct['area'] < (10 * 10):
                    #print('area:', object_struct['area'])
                    object_struct['difficult'] = 1
                objects.append(object_struct)
            else:
                break
    return objects
def voc_ap(rec, prec, use_07_metric=False):
    """ ap = voc_ap(rec, prec, [use_07_metric])
    Compute VOC AP given precision and recall.
    If use_07_metric is true, uses the
    VOC 07 11 point method (default:False).
    """
    if use_07_metric:
        # 11 point metric
        ap = 0.
        for t in np.arange(0., 1.1, 0.1):
            if np.sum(rec >= t) == 0:
                p = 0
            else:
                p = np.max(prec[rec >= t])
            ap = ap + p / 11.
    else:
        # correct AP calculation
        # first append sentinel values at the end
        mrec = np.concatenate(([0.], rec, [1.]))
        mpre = np.concatenate(([0.], prec, [0.]))

        # compute the precision envelope
        for i in range(mpre.size - 1, 0, -1):
            mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

        # to calculate area under PR curve, look for points
        # where X axis (recall) changes value
        i = np.where(mrec[1:] != mrec[:-1])[0]

        # and sum (\Delta recall) * prec
        ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap
def parse_ucas_gt(filename):
    objects = []
    with  open(filename, 'r') as f:

        #print('filename:', filename)
        lines = f.readlines()
        splitlines = [x.strip().split() for x in lines]
        basename = os.path.basename(os.path.splitext(filename)[0])
        #print('basename:', basename)
        numer = int(basename[1:])
        if (numer <= 510):
            classname = 'small-vehicle'
        else:
            classname = 'plane'

        for splitline in splitlines:
            object_struct = {}
            object_struct['name'] = classname
            #print('splitline: ', splitline)
            x, y, w, h = float(splitline[9]), float(splitline[10]), float(splitline[11]), float(splitline[12])
            object_struct['bbox'] = [x, y, x + w, y + h]
            object_struct['difficult'] = 0
            objects.append(object_struct)
    return objects
def voc_eval(detpath,
             annopath,
             imagesetfile,
             classname,
            # cachedir,
             ovthresh=0.5,
             use_07_metric=False):
    """rec, prec, ap = voc_eval(detpath,
                                annopath,
                                imagesetfile,
                                classname,
                                [ovthresh],
                                [use_07_metric])
    Top level function that does the PASCAL VOC evaluation.
    detpath: Path to detections
        detpath.format(classname) should produce the detection results file.
    annopath: Path to annotations
        annopath.format(imagename) should be the xml annotations file.
    imagesetfile: Text file containing the list of images, one image per line.
    classname: Category name (duh)
    cachedir: Directory for caching the annotations
    [ovthresh]: Overlap threshold (default = 0.5)
    [use_07_metric]: Whether to use VOC07's 11 point AP computation
        (default False)
    """
    # assumes detections are in detpath.format(classname)
    # assumes annotations are in annopath.format(imagename)
    # assumes imagesetfile is a text file with each line an image name
    # cachedir caches the annotations in a pickle file

    # first load gt
    #if not os.path.isdir(cachedir):
     #   os.mkdir(cachedir)
    #cachefile = os.path.join(cachedir, 'annots.pkl')
    # read list of images
    with open(imagesetfile, 'r') as f:
        lines = f.readlines()
    imagenames = [x.strip() for x in lines]
    #print('imagenames: ', imagenames)
    #if not os.path.isfile(cachefile):
        # load annots
    recs = {}
    for i, imagename in enumerate(imagenames):
        #print('parse_files name: ', annopath.format(imagename))
        #recs[imagename] = parse_gt(annopath.format(imagename))
        recs[imagename] = parse_ucas_gt(annopath.format(imagename))
        #if i % 100 == 0:
         #   print ('Reading annotation for {:d}/{:d}'.format(
          #      i + 1, len(imagenames)) )
        # save
        #print ('Saving cached annotations to {:s}'.format(cachefile))
        #with open(cachefile, 'w') as f:
         #   cPickle.dump(recs, f)
    #else:
        # load
        #with open(cachefile, 'r') as f:
         #   recs = cPickle.load(f)

    # extract gt objects for this class
    class_recs = {}
    npos = 0
    for imagename in imagenames:
        R = [obj for obj in recs[imagename] if obj['name'] == classname]
        bbox = np.array([x['bbox'] for x in R])
        difficult = np.array([x['difficult'] for x in R]).astype(np.bool)
        det = [False] * len(R)
        npos = npos + sum(~difficult)
        class_recs[imagename] = {'bbox': bbox,
                                 'difficult': difficult,
                                 'det': det}

    # read dets
    detfile = detpath.format(classname)
    with open(detfile, 'r') as f:
        lines = f.readlines()

    splitlines = [x.strip().split(' ') for x in lines]
    image_ids = [x[0] for x in splitlines]
    confidence = np.array([float(x[1]) for x in splitlines])

    #print('check confidence: ', confidence)

    BB = np.array([[float(z) for z in x[2:]] for x in splitlines])

    # sort by confidence
    sorted_ind = np.argsort(-confidence)
    sorted_scores = np.sort(-confidence)

    #print('check sorted_scores: ', sorted_scores)
    #print('check sorted_ind: ', sorted_ind)
    BB = BB[sorted_ind, :]
    image_ids = [image_ids[x] for x in sorted_ind]
    #print('check imge_ids: ', image_ids)
    #print('imge_ids len:', len(image_ids))
    # go down dets and mark TPs and FPs
    nd = len(image_ids)
    tp = np.zeros(nd)
    fp = np.zeros(nd)
    for d in range(nd):
        R = class_recs[image_ids[d]]
        bb = BB[d, :].astype(float)
        ovmax = -np.inf
        BBGT = R['bbox'].astype(float)

        if BBGT.size > 0:
            # compute overlaps
            # intersection
            ixmin = np.maximum(BBGT[:, 0], bb[0])
            iymin = np.maximum(BBGT[:, 1], bb[1])
            ixmax = np.minimum(BBGT[:, 2], bb[2])
            iymax = np.minimum(BBGT[:, 3], bb[3])
            iw = np.maximum(ixmax - ixmin + 1., 0.)
            ih = np.maximum(iymax - iymin + 1., 0.)
            inters = iw * ih

            # union
            uni = ((bb[2] - bb[0] + 1.) * (bb[3] - bb[1] + 1.) +
                   (BBGT[:, 2] - BBGT[:, 0] + 1.) *
                   (BBGT[:, 3] - BBGT[:, 1] + 1.) - inters)

            overlaps = inters / uni
            ovmax = np.max(overlaps)
            jmax = np.argmax(overlaps)

        if ovmax > ovthresh:
            if not R['difficult'][jmax]:
                if not R['det'][jmax]:
                    tp[d] = 1.
                    R['det'][jmax] = 1
                else:
                    fp[d] = 1.
        else:
            fp[d] = 1.

    # compute precision recall

    #print('check fp:', fp)
    #print('check tp', tp)


    print('npos num:', npos)
    fp = np.cumsum(fp)
    tp = np.cumsum(tp)

    #print('fp num:', fp)
    #print('tp num:', tp)
    #print('np num:', np)
    rec = tp / float(npos)
    # avoid divide by zero in case the first detection matches a difficult
    # ground truth
    prec = tp / np.maximum(tp + fp, np.finfo(np.float64).eps)
    ap = voc_ap(rec, prec, use_07_metric)

    return rec, prec, ap

def main():
    detpath = r'E:\downloaddataset\CarPlane\results\bod-valid-car-480000-nms\comp4_det_test_{:s}.txt'
    #annopath = r'G:\voc_eval\GFformatPascal\{:s}.txt'
    annopath = r'E:\downloaddataset\CarPlane\label2\{:s}.txt'
    imagesetfile = r'E:\downloaddataset\CarPlane\test.txt'
    #classnames = ['plane', 'bridge', 'storage', 'ship', 'harbor']
    #classnames = ['0A', '0B', '0C', '1', '2', '3', '4A', '4B', '4C', '5A', '5B', '6', '7', '8', '9', '10'
     #   , '11', '12', '13', '14', '15', '16', '18A']
    #classnames = ['plane', 'baseball-diamond', 'bridge', 'ground-track-field', 'small-vehicle', 'large-vehicle', 'ship', 'tennis-court',
     #          'baseketball-court', 'storage-tank',  'soccer-ball-field', 'turntable', 'harbor', 'swimming-pool', 'helicopter']

    classnames = ['plane', 'small-vehicle']

    #classnames = ['0A']
    #classes = [datamap2[x] for x in classnames]
    classaps = []
    map = 0
    for classname in classnames:
        print('classname:', classname)
        rec, prec, ap = voc_eval(detpath,
             annopath,
             imagesetfile,
             classname,
             ovthresh=0.5,
             use_07_metric=True)
        map = map + ap
        #print('rec: ', rec, 'prec: ', prec, 'ap: ', ap)
        print('ap: ', ap)
        classaps.append(ap)
        plt.figure(figsize=(8,4))
        plt.xlabel('recall')
        plt.ylabel('precision')
        plt.plot(rec, prec)
        plt.show()
    map = map/len(classnames)
    print('map:', map)
    #classout = ' && '.join(classes)
    #print('classout: ', classout)
    classaps = 100*np.array(classaps)
    print('classaps: ', classaps)
    #print('aps:', ' '.join(map(str, classaps)))
if __name__ == '__main__':
    main()