import hdt
import gzip, sys
import pandas as pd
import numpy as np

import kgbench as kg

from tqdm import tqdm

"""
Extracts target labels.

"""

## Map from dataset category to coarse-grained classes.
map = {}

map['http://purl.org/collections/nl/am/t-14592'] = 'Books and Documents'
# boekencollectie 	3479
# Book collection

map['http://purl.org/collections/nl/am/t-15459'] = 'Decorative art'
# meubelcollectie 	3206
# Furniture

map['http://purl.org/collections/nl/am/t-15573'] = 'Decorative art'
# glascollectie 	1028
# Glass

map['http://purl.org/collections/nl/am/t-15579'] = 'Decorative art'
# textielcollectie 	7366
# Textiles

map['http://purl.org/collections/nl/am/t-15606'] = 'Decorative art'
# keramiekcollectie 	5152

map['http://purl.org/collections/nl/am/t-16469'] = 'Metallic art'
# onedele metalen collectie 	797
# Non-noble metals

map['http://purl.org/collections/nl/am/t-22503'] = 'Prints'
# prentencollectie 	22048
# Prints

map['http://purl.org/collections/nl/am/t-22504'] = 'Photographs'
# fotocollectie 	1563
# Photographs

map['http://purl.org/collections/nl/am/t-22505'] = 'Drawings'
# tekeningencollectie 	5455
# Drawings

map['http://purl.org/collections/nl/am/t-22506'] = 'Paintings'
# schilderijencollectie 	2672
# Paintings

map['http://purl.org/collections/nl/am/t-22507'] = 'Decorative art'
# beeldencollectie 	943
# Sculpture (?)

map['http://purl.org/collections/nl/am/t-22508'] = 'Metallic art'
# edele metalencollectie 	3533
# Noble metals

map['http://purl.org/collections/nl/am/t-22509'] = 'Historical artifacts'
# penningen- en muntencollectie 	6440
# Coins etc.

map['http://purl.org/collections/nl/am/t-28650'] = 'Historical artifacts'
# archeologiecollectie 	582
# Archeaological artifacts

map['http://purl.org/collections/nl/am/t-23765'] = 'Books and Documents'
# documentencollectie 	533
# Document collection

map['http://purl.org/collections/nl/am/t-31940'] = 'Metallic art'
# -- Onedele collectie 	3
# A small category containing only room numbers from a defunct men's club

map['http://purl.org/collections/nl/am/t-32052'] = 'Historical artifacts'
# -- maten en gewichtencollectie 	536
# Measures and weight

map['http://purl.org/collections/nl/am/t-5504'] = 'Decorative art'
# -- kunstnijverheidcollectie 	8087
# Arts and crafts

complete = hdt.HDTDocument('am-combined.hdt')

# the class relation
rel = 'http://purl.org/collections/nl/am/objectCategory'

data = []
triples, c = complete.search_triples('', rel, '')

for i, (s, _, o) in enumerate(triples):
    data.append([s, o])

df = pd.DataFrame(data, columns=['instance', 'label_original'])

df['cls_label'] = df.label_original.map(map)

df.cls_label = pd.Categorical(df.cls_label)
df['cls'] = df.cls_label.cat.codes

df.to_csv('all.csv', sep=',', index=False, header=True)
print('Created dataframe. Class frequencies:')
print(df.cls_label.value_counts(normalize=True))
print(df.cls_label.value_counts(normalize=True))

# * Split train, validation and test sets

# fixed seed for deterministic output
np.random.seed(0)

meta_size = 20_000
test_size = 20_000
val_size = 20_000
train_size =  len(df) - test_size - val_size - meta_size

print(f'train {train_size}, val {val_size}, test {test_size}, meta {meta_size}')

bin = np.concatenate( [
    np.full((train_size,), 0),
    np.full((val_size,), 1),
    np.full((test_size,), 2),
    np.full((meta_size,), 3) ], axis=0)

np.random.shuffle(bin) # in place

train = df[bin == 0]
train.to_csv('training.csv', sep=',', index=False, header=True)

val = df[bin == 1]
val.to_csv('validation.csv', sep=',', index=False, header=True)

test = df[bin == 2]
test.to_csv('testing.csv', sep=',', index=False, header=True)

test = df[bin == 3]
test.to_csv('meta-testing.csv', sep=',', index=False, header=True)

print('created train, val, test, meta split.')

stripped = hdt.HDTDocument('am-stripped.hdt')
triples, c = stripped.search_triples('', '', '')

entities = set()
relations = set()

print('Creating dictionaries.')
for s, p, o in tqdm(triples, total=c):
    entities.add(str(s))
    entities.add(str(o))
    relations.add(str(p))

i2e = list(entities)
i2r = list(relations)

i2e.sort(); i2r.sort()

df = pd.DataFrame(enumerate(i2e), columns=['index', 'label'])
df.to_csv('entities.int.csv', index=False, header=True)

df = pd.DataFrame(enumerate(i2r), columns=['index', 'label'])
df.to_csv('relations.int.csv', index=False, header=True)

e2i = {e:i for i, e in enumerate(i2e)}
r2i = {r:i for i, r in enumerate(i2r)}

for file in ['training', 'testing', 'validation', 'meta-testing']:
    df = pd.read_csv(file + '.csv')
    classes = df.cls
    instances = df.instance
    intinstances = instances.map(e2i)

    pd.concat([intinstances, classes], axis=1).to_csv(file + '.int.csv', index=False, header=False)

## Convert stripped triples to integer triples

triples, c = stripped.search_triples('', '', '')
print('Writing integer triples.')
with gzip.open('triples.int.csv.gz', 'wt') as file:

    for s, p, o in tqdm(triples, total=c):
        assert p != 'http://purl.org/collections/nl/am/objectCategory'
        assert p != 'http://purl.org/collections/nl/am/material'

        file.write(f'{e2i[s]}, {r2i[p]}, {e2i[o]}\n')







