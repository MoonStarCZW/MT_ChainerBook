import glob

import numpy as np
import chainer
from chainer import cuda, Function, gradient_check, Variable, optimizers, serializers, utils
from chainer import Link, Chain, ChainList
import chainer.functions as F
import chainer.links as L

jvocab = {}
# jlines = open('jp.txt').read().split('\n')
# for i in range(len(jlines)):
#     lt = jlines[i].split()
#     for w in lt:
#         if w not in jvocab:
#             jvocab[w] = len(jvocab)
# jvocab['<eos>'] = len(jvocab)
# jv = len(jvocab)

jlines = glob.glob('ruby_input/*.rb')
for i in range(len(jlines)):
    f = open(jlines[i], 'r').read().split('\n')
    for line in f:
        if line not in jvocab:
            jvocab[line] = len(jvocab)
jvocab["<eos>"] = len(jvocab)
jv = len(jvocab)

evocab = {}
id2wd = {}
# elines = open('eng.txt').read().split('\n')
# for i in range(len(elines)):
#     lt = elines[i].split()
#     for w in lt:
#         if w not in evocab:
#             val = len(evocab)
#             id2wd[val] = w
#             evocab[w] = val
# val = len(evocab)
# id2wd[val] = '<eos>'
# evocab['<eos>'] = val
# ev = len(evocab)

elines = glob.glob('python_output/*.py')
for i in range(len(elines)):
    f = open(elines[i], 'r').read().split('\n')
    for line in f:
        if line not in evocab:
            val = len(evocab)
            id2wd[val] = line
            evocab[line] = val
evocab["<eos>"] = len(evocab)
ev = len(evocab)


class MyMT(chainer.Chain):
    def __init__(self, jv, ev, k):
        super(MyMT, self).__init__(
            # embedx=L.EmbedID(jv, k),
            # embedy=L.EmbedID(ev, k),
            # H=L.LSTM(k, k),
            # W=L.Linear(k, ev),
        )
        with self.init_scope():
            self.embedx = L.EmbedID(jv, k)
            self.embedy = L.EmbedID(ev, k)
            self.H = L.LSTM(k, k)
            self.W = L.Linear(k, ev)

    def __call__(self, jline, eline):
        # self.H.reset_state()
        for i in range(len(jline)):
            wid = jvocab[jline[i]]
            x_k = self.embedx(Variable(np.array([wid], dtype=np.int32)))
            h = self.H(x_k)
        x_k = self.embedx(Variable(np.array([jvocab['<eos>']], dtype=np.int32)))
        tx = Variable(np.array([evocab[eline[0]]], dtype=np.int32))
        h = self.H(x_k)
        accum_loss = F.softmax_cross_entropy(self.W(h), tx)
        for i in range(1, len(eline)):
            wid = evocab[eline[i]]
            x_k = self.embedy(Variable(np.array([wid], dtype=np.int32)))
            next_wid = evocab['<eos>'] if (i == len(eline) - 1) else evocab[eline[i + 1]]
            tx = Variable(np.array([next_wid], dtype=np.int32))
            h = self.H(x_k)
            loss = F.softmax_cross_entropy(self.W(h), tx)
            accum_loss = loss if accum_loss is None else accum_loss + loss
        return accum_loss


def mt(model, jline):
    # model.H.reset_state()
    for i in range(len(jline)):
        wid = jvocab[jline[i]]
        x_k = model.embedx(Variable(np.array([wid], dtype=np.int32)))
        h = model.H(x_k)
    x_k = model.embedx(Variable(np.array([jvocab['<eos>']], dtype=np.int32)))
    h = model.H(x_k)
    wid = np.argmax(F.softmax(model.W(h)).data[0])
    if wid in id2wd:
        print(id2wd[wid], end="\n")
    else:
        print(wid, end="\n")
    loop = 0
    while (wid != evocab['<eos>']) and (loop <= 30):
        x_k = model.embedy(Variable(np.array([wid], dtype=np.int32)))
        h = model.H(x_k)
        wid = np.argmax(F.softmax(model.W(h)).data[0])
        if wid in id2wd:
            print(id2wd[wid], end="\n")
        else:
            print(wid, end="\n")
        loop += 1
    print()


# jlines = open('jp-test.txt').read().split('\n')
jlines = glob.glob('ruby_input/*.rb')
demb = 100

for epoch in range(100):
    model = MyMT(jv, ev, demb)
    filename = "model/mt-" + str(epoch) + ".model"
    serializers.load_npz(filename, model)
    # for i in range(len(jlines) - 1):
    #     jln = jlines[i].split()
    #     jlnr = jln[::-1]
    #     print(epoch, ":")
    #     mt(model, jlnr)


    # for i in range(len(jlines) - 1):
    #     jln = open(jlines[i], 'r')  # file
    #     jlnr = jln.read().split('\n')  # line
    #     jlnr = jlnr[::-1]
    #     print(epoch, ":")
    #     mt(model, jlnr)


    jln = open('ruby_input/helloworld.rb')
    jlnr = jln.read().split('\n')  # line
    jlnr = jlnr[::-1]
    print(epoch, ":")
    mt(model, jlnr)
