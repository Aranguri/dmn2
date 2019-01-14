import itertools
import tensorflow as tf
from preprocess import BabiTask
from model import DMNCell
import numpy as np
from utils import *

learning_rate = 1e-4
batch_size = 64
embeddings_size = 256
h_size = 512
similarity_layer_size = 512
output_hidden_size = 512
debug_steps = 10
alpha, beta = 0, 1
gates_acc_threshold = .97

babi_task = BabiTask(batch_size)
input_length, question_length, vocab_size = babi_task.get_lengths()

input_ids = tf.placeholder(tf.int32, shape=(None, input_length))
question_ids = tf.placeholder(tf.int32, shape=(None, question_length))
answer = tf.placeholder(tf.int32, shape=(None, vocab_size))
supporting = tf.placeholder(tf.int32, shape=(None, None))

embeddings = tf.get_variable('embeddings', shape=(vocab_size, embeddings_size))
input = tf.nn.embedding_lookup(embeddings, input_ids)
question = tf.nn.embedding_lookup(embeddings, question_ids)
eos_vector = tf.nn.embedding_lookup(embeddings, babi_task.eos_vector)

dmn_cell = DMNCell(eos_vector, vocab_size, h_size, similarity_layer_size,
                   output_hidden_size, learning_rate, alpha, beta,
                   gates_acc_threshold)
loss, data = dmn_cell.run(input, question, answer, supporting)
minimize = dmn_cell.minimize_op(loss)

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    tr_loss, tr_gates_loss, tr_gates_acc = {}, {}, {}
    tr_output_loss, tr_output_acc = {}, {}
    dev_loss, dev_gates_loss, dev_gates_acc = {}, {}, {}
    dev_output_loss, dev_output_acc = {}, {}

    for j in itertools.count():
        input_, question_, answer_, sup_ = babi_task.next_batch()
        feed_dict = {input_ids: input_, question_ids: question_, answer: answer_, supporting: sup_}
        tr_loss[j], data_, _ = sess.run([loss, data, minimize], feed_dict)
        tr_output_loss[j], tr_gates_loss[j], tr_output_acc[j], tr_gates_acc[j] = data_

        if j % debug_steps == 0:
            input_, question_, answer_, sup_ = babi_task.dev_data()
            feed_dict = {input_ids: input_, question_ids: question_, answer: answer_, supporting: sup_}
            dev_loss[j/debug_steps], data_ = sess.run([loss, data], feed_dict)
            dev_output_loss[j], dev_gates_loss[j], dev_output_acc[j], dev_gates_acc[j] = data_

            tol, toa = list(tr_output_loss.values()), list(tr_output_acc.values())
            tgl, tga = list(tr_gates_loss.values()), list(tr_gates_acc.values())
            dol, doa = list(dev_output_loss.values()), list(dev_output_acc.values())
            dgl, dga = list(dev_gates_loss.values()), list(dev_gates_acc.values())
            print(f'{j}) TRAIN: Output: Loss: {np.mean(tol[-10:])}. Acc: {np.mean(toa[-10:])}. Gates: Loss: {np.mean(tgl[-10:])}. Acc: {np.mean(tga[-10:])}')
            print(f'{j}) DEV  : Gates : Loss: {np.mean(dol[-10:])}. Acc: {np.mean(doa[-10:])}. Gates: Loss: {np.mean(dgl[-10:])}. Acc: {np.mean(dga[-10:])} \n')
            # smooth_plot(gates_acc)
            # smooth_plot(tr_loss)
