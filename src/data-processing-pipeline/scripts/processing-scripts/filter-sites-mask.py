#!/usr/bin/env python
# coding: utf-8
# %%

# %%

import sys
import argparse
import numpy as np                          # numerical tools
from timeit import default_timer as timer   # timer for performance
import os
import subprocess
import shutil
import data_processing as dp
import pandas as pd

REF_TAG = 'EPI_ISL_402125'
NUC     = ['-', 'A', 'C', 'G', 'T']
START_IDX = 150
END_IDX   = 29690


def find_site_index_file(filepath):
    """ Given a sequence file find the correct corresponding file that has the site names"""
    directory, file = os.path.split(filepath)
    if file.find('---')==-1:
        return filepath[:-4] + '-sites.csv'
    else:
        return filepath[:filepath.find('---')] + '-sites.csv'   


def get_data(file, get_seqs=True):
    """ Given a sequence file, get the sequences, dates, and mutant site labels"""
    data      = pd.read_csv(file)
    if not get_seqs:
        sequences = None
    else:
        sequences = np.array([np.array(list(i)) for i in list(data['sequence'])])
    dates     = list(data['date'])
    sub_dates = list(data['submission date'])
    index_file = find_site_index_file(file)
    index_data = pd.read_csv(index_file)
    mut_sites  = list(index_data['mutant_sites'])
    ref_sites  = list(index_data['ref_sites'])
    dic = {
        'ref_sites' : ref_sites,
        'mutant_sites' : mut_sites,
        'sequences' : sequences[:-1],
        'dates' : dates[:-1],
        'submission_dates' : sub_dates[:-1]
    }
    return dic


def moving_average(freq, window=9):
    """ Calculates a moving average for a frequency array. """
    ret = np.cumsum(freq, axis=0)
    ret[window:] = ret[window:] - ret[:-window]
    result = ret[window - 1:] / window
    return result

def main(args):
    """ Eliminate sites that don't have more than min_count genomes containing the mutation in the whole time series"""
    
    parser = argparse.ArgumentParser(description='Selection coefficients inference')
    parser.add_argument('-o',             type=str,    default=None,           help='output directory')
    parser.add_argument('--max_dir',      type=str,    default=None,           help='directory containing maximum frequencies for each site')
    parser.add_argument('--mask_dir',      type=str,    default=None,           help='directory for writing masks')
    parser.add_argument('--input',        type=str,    default=None,           help='input file containing sequence data')
    parser.add_argument('--min_count',    type=int,    default=5,              help='the maximum frequency at which to cutoff sites')
    parser.add_argument('--min_freq',     type=float,  default=0.01,           help='the minimum regional frequency required in order to keep a site')
    parser.add_argument('--freqWindow',   type=int,    default=5,              help='the number of consecutive days in which the frequency must be higher than min_freq')
    parser.add_argument('--smoothWindow', type=int,    default=2,              help='the number of days over which to smooth the frequencies')
    parser.add_argument('--refFile',      type=str,    default='ref-index.csv',help='the file containing the reference index and nucleotides')
    parser.add_argument('--gapFile',      type=str,    default='gap-list.npy', help='the file containing sites that have known deletions')
    
    arg_list = parser.parse_args(args)
    
    out_dir   = arg_list.o        
    max_dir   = arg_list.max_dir
    mask_dir  = arg_list.mask_dir
    file      = arg_list.input
    min_count = arg_list.min_count
    min_freq  = arg_list.min_freq
    window    = arg_list.freqWindow
    smooth_window = arg_list.smoothWindow
    
    ref_df = pd.read_csv(arg_list.refFile)
    index  = list(ref_df['ref_index'])
    nucs   = np.array(ref_df['nucleotide'])
    
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
        
    gap_list = np.load(arg_list.gapFile, allow_pickle=True)
    
    file_tail = os.path.split(file)[-1]
    if 'sites' in file:
        sys.exit()
    print(file)
    freq_data  = np.load(os.path.join(max_dir, file_tail), allow_pickle=True)
    mut_counts = freq_data['mut_counts']
    freqs      = freq_data['frequency']
    seq_data   = get_data(file)
    refs       = np.array(seq_data['ref_sites'])
    muts       = np.array(seq_data['mutant_sites'])
    if  window >= len(freqs):
        window = len(freqs) - 2
    new_counts = []
    for i in range(len(mut_counts)):
        new_counts.append([mut_counts[i][j] for j in range(len(mut_counts[i])) if NUC[j]!=nucs[index.index(str(refs[i]))]])
    new_counts = [np.sum(i) for i in new_counts]
    times      = seq_data['dates']
    freq_mask  = np.any(freqs > min_freq, axis=2)
    freq_mask  = np.any([np.all(freq_mask[i:i+window], axis=0) for i in range(len(freq_mask)-window)], axis=0)
    mask       = np.logical_and(np.array(new_counts)>min_count, freq_mask)

    
    mask_file = os.path.join(mask_dir, f'{file_tail[:-4]}-mask.npy')
    np.save(mask_file, mask)

    seqs_new = np.array([i[mask] for i in seq_data['sequences']])
    muts_new = muts[mask]
    refs_new = refs[mask]
    
    idxs = []
    for i in refs_new:
        idx, gap_num = dp.separate_label_idx(str(i))
        idxs.append(int(idx))
    idxs = np.array(idxs)
    mask = np.array([True if (idxs[i] > START_IDX and idxs[i] < END_IDX) else False for i in range(len(idxs))])

    refs_new = refs_new[mask]
    seqs_new = [np.array(i)[mask] for i in seqs_new]

    seqs_new = [''.join(list(i)) for i in seqs_new]
  
    print(len(muts_new))

    out_file = os.path.join(out_dir, file_tail)
    data = {
        'submission_date' : seq_data['submission_dates'],
        'date' : times,
        'sequence' : seqs_new
    }
    df = pd.DataFrame(data=data)
    df.to_csv(out_file, index=False)
        
    sites_data = {'ref_sites' : refs_new}
    df2 = pd.DataFrame(data=sites_data)
    df2.to_csv(out_file[:-4] + '-sites.csv', index=False)
                
    
if __name__ == '__main__': 
    main(sys.argv[1:])
